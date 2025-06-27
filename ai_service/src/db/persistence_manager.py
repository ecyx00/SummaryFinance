"""
Persistence Manager Module

Bu modül, zenginleştirilmiş haber verilerini PostgreSQL veritabanına kaydetmeye
yarayan PersistenceManager sınıfını içerir.
"""

import logging
import psycopg2
import psycopg2.pool
import psycopg2.extras
import pgvector.psycopg2
from typing import Dict, Any, List, Optional, Tuple
from ..core.config import settings

# Logger yapılandırması
logger = logging.getLogger(__name__)

# İşlem durumu sabitleri
PROCESSING_SUCCESS = "PROCESSING_SUCCESS"
PROCESSING_PARTIAL_SUCCESS = "PROCESSING_PARTIAL_SUCCESS" 
PROCESSING_FAILED = "PROCESSING_FAILED"
PROCESSING_PENDING = "PENDING"


class PersistenceManager:
    """
    FeatureExtractor'dan gelen zenginleştirilmiş haber verilerini veritabanına kaydeden sınıf.
    
    Bu sınıf, varlıkların (entitites) eklenmesi/güncellenmesi, gömme vektörlerinin (embedding vectors)
    kaydedilmesi ve işlem loglarının tutulması gibi görevleri yerine getirir.
    """
    
    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        """
        PersistenceManager sınıfını başlatır ve bir bağlantı havuzu oluşturur.
        
        Args:
            min_conn: Bağlantı havuzundaki minimum bağlantı sayısı
            max_conn: Bağlantı havuzundaki maksimum bağlantı sayısı
        """
        self.conn_pool = None
        try:
            logger.info(f"Veritabanı bağlantı havuzu oluşturuluyor (Min: {min_conn}, Max: {max_conn})...")
            
            # Bağlantı havuzunu oluştur
            self.conn_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB
            )
            
            logger.info("Veritabanı bağlantı havuzu başarıyla oluşturuldu")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı havuzu oluştururken hata: {e}")
            raise
            
    def __del__(self):
        """Sınıf silindiğinde bağlantı havuzunu kapat"""
        if self.conn_pool:
            self.conn_pool.closeall()
            logger.info("Veritabanı bağlantı havuzu kapatıldı")
            
    def save_features(self, enriched_item: Dict[str, Any], model_version: str) -> str:
        """
        Zenginleştirilmiş haber öğesini ve ilişkili varlıkları veritabanına kaydeder.
        
        Args:
            enriched_item: FeatureExtractor'dan gelen zenginleştirilmiş haber verileri
                           Gerekli alanlar: id, entities, embedding_vector
            model_version: Gömme vektörü oluşturmak için kullanılan modelin sürümü
            
        Returns:
            str: İşlem durumu (PROCESSING_SUCCESS, PROCESSING_PARTIAL_SUCCESS veya PROCESSING_FAILED)
        """
        if not enriched_item.get("id"):
            logger.error("enriched_item 'id' alanını içermiyor, veritabanına kayıt yapılamadı")
            return PROCESSING_FAILED
            
        news_id = enriched_item["id"]
        
        # Varlıklar ve gömme vektörü yoksa kısmi başarı durumu
        has_entities = enriched_item.get("entities") is not None
        has_embedding = enriched_item.get("embedding_vector") is not None
        
        if not has_entities and not has_embedding:
            logger.warning(f"Haber ID {news_id} için varlık ve gömme vektörü yok, işlem atlanıyor")
            return PROCESSING_FAILED
            
        # İşlem durumunu belirle ve kısmi başarı nedenleri için daha ayrıntılı bilgi
        status = PROCESSING_SUCCESS
        error_details = []
        
        if not has_entities:
            error_details.append("Entity extraction failed or no entities found")
            
        if not has_embedding:
            error_details.append("Embedding vector generation failed")
            
        if error_details:
            status = PROCESSING_PARTIAL_SUCCESS
            error_message = "; ".join(error_details)
            logger.warning(f"Haber ID {news_id} için kısmi başarı: {error_message}")
        else:
            error_message = None
            
        # Veritabanından bir bağlantı al
        conn = None
        try:
            conn = self.conn_pool.getconn()
            # pgvector eklentisini kaydet
            pgvector.psycopg2.register_vector(conn)
            
            # Auto-commit'i kapat, işlemleri manuel kontrol edeceğiz
            conn.autocommit = False
            
            # Adım 1: Varlıkları kaydet/güncelle
            if has_entities:
                entity_ids = self._save_entities(conn, news_id, enriched_item["entities"])
                logger.info(f"Haber ID {news_id} için {len(entity_ids)} adet varlık kaydedildi")
                
            # Adım 2: İşlemi logla ve gömme vektörünü güncelle
            self._update_news_and_log(
                conn, 
                news_id, 
                status, 
                model_version, 
                enriched_item.get("embedding_vector"),
                error_message if status == PROCESSING_PARTIAL_SUCCESS else None
            )
            
            # İşlemi onayla ve commit et
            conn.commit()
            logger.info(f"Haber ID {news_id} için veriler başarıyla kaydedildi")
            return status
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Haber ID {news_id} için veri kaydetme sırasında hata: {e}")
            
            # Hata durumunda işlem logunu güncelle
            try:
                if conn:
                    conn.autocommit = True
                    self._log_processing_error(conn, news_id, str(e)[:255])
            except Exception as log_error:
                logger.error(f"Hata logu kaydederken ikincil hata: {log_error}")
                
            return PROCESSING_FAILED
            
        finally:
            if conn:
                self.conn_pool.putconn(conn)
                
    def _save_entities(self, conn, news_id: int, entities: Dict[str, List[str]]) -> List[int]:
        """
        Varlıkları veritabanına kaydeder/günceller ve ilişkileri oluşturur.
        
        Args:
            conn: Veritabanı bağlantısı
            news_id: Haber ID'si
            entities: Varlık tipleri ve isimleri
            
        Returns:
            Eklenen varlıkların ID'lerini içeren liste
        """
        entity_ids = []
        with conn.cursor() as cur:
            # Her bir varlık tipi ve adı için
            for entity_type, entity_names in entities.items():
                for entity_name in entity_names:
                    if not entity_name or not entity_type:
                        continue
                    
                    # Varlığı ekle veya var olanı getir (UPSERT işlemi)
                    # NOT: Veritabanı şemasında updated_at sütunu yoksa, bu satırı kaldırın
                    cur.execute("""
                        INSERT INTO entities (name, type) 
                        VALUES (%s, %s)
                        ON CONFLICT (name, type) DO NOTHING
                        RETURNING id
                    """, (entity_name, entity_type))
                    
                    entity_id = cur.fetchone()[0]
                    entity_ids.append(entity_id)
                    
                    # Haber-Varlık ilişkisini oluştur
                    cur.execute("""
                        INSERT INTO article_entities (news_id, entity_id)
                        VALUES (%s, %s)
                        ON CONFLICT (news_id, entity_id) DO NOTHING
                    """, (news_id, entity_id))
        
        return entity_ids
        
    def _update_news_and_log(
            self, 
            conn, 
            news_id: int, 
            status: str, 
            model_version: str,
            embedding_vector: Optional[List[float]] = None,
            error_message: Optional[str] = None
        ) -> None:
        """
        Haber tablosunu ve işlem loglarını günceller.
        
        Args:
            conn: Veritabanı bağlantısı
            news_id: Haber ID'si
            status: İşlem durumu
            model_version: Gömme vektörü modeli sürümü
            embedding_vector: Gömme vektörü
            error_message: Hata mesajı
        """
        with conn.cursor() as cur:
            # İşlem logunu güncelle - şemaya uygun olarak
            # NOT: şemayı kontrol edin ve gerekirse SQL sorgusunu uyarlayın
            
            # Error message parametresini hazırla
            query_params = [news_id, status, model_version]
            
            # Temel sorgu
            query = """
                INSERT INTO ai_processing_log 
                (news_id, status, embedding_model_version{error_field})
                VALUES (%s, %s, %s{error_placeholder})
                ON CONFLICT (news_id) DO UPDATE
                SET status = %s,
                    embedding_model_version = %s{error_update}
            """
            
            # Hata mesajı varsa ekleme yap
            if error_message:
                query = query.format(
                    error_field=", error_message",
                    error_placeholder=", %s",
                    error_update=", error_message = %s"
                )
                query_params.extend([error_message, status, model_version, error_message])
            else:
                query = query.format(
                    error_field="",
                    error_placeholder="",
                    error_update=""
                )
                query_params.extend([status, model_version])
                
            cur.execute(query, query_params)
            
            # Gömme vektörü varsa haberi güncelle
            if embedding_vector is not None:
                cur.execute("""
                    UPDATE news
                    SET embedding_vector = %s
                    WHERE id = %s
                """, (embedding_vector, news_id))
                
    def _log_processing_error(self, conn, news_id: int, error_message: str) -> None:
        """
        İşlem hatasını loga kaydeder.
        
        Args:
            conn: Veritabanı bağlantısı
            news_id: Haber ID'si
            error_message: Hata mesajı
        """
        try:
            with conn.cursor() as cur:
                # Şemaya uygun olarak sadeleştirilmiş sorgu
                cur.execute("""
                    INSERT INTO ai_processing_log 
                    (news_id, status, error_message)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (news_id) DO UPDATE
                    SET status = %s,
                        error_message = %s
                """, (news_id, PROCESSING_FAILED, error_message, 
                      PROCESSING_FAILED, error_message))
        except Exception as e:
            logger.error(f"Hata logu kaydederken hata: {e}")
            
    def fetch_unprocessed_news(self, limit: int = 100) -> List[Dict]:
        """
        İşlenmemiş veya beklemedeki haberleri veritabanından çeker.
        
        İşlenmemiş haber kriterleri:
        - ai_processing_log tablosunda kaydı olmayan haberler
        - Status değeri PENDING olan haberler
        
        Args:
            limit: Çekilecek maksimum haber sayısı
            
        Returns:
            List[Dict]: İşlenmemiş haberlerin listesi
        """
        unprocessed_news = []
        conn = None
        
        try:
            # Bağlantı havuzundan bir bağlantı al
            conn = self.conn_pool.getconn()
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # İşlenmemiş haberleri çeken SQL sorgusu
                cur.execute("""
                    SELECT n.id, n.url, n.title, n.source
                    FROM news n
                    LEFT JOIN ai_processing_log l ON n.id = l.news_id
                    WHERE l.news_id IS NULL OR l.status = %s
                    LIMIT %s
                """, (PROCESSING_PENDING, limit))
                
                rows = cur.fetchall()
                for row in rows:
                    # DictCursor ile çekilen satırları dict'e dönüştürme
                    unprocessed_news.append(dict(row))
                    
                logger.info(f"İşlenmemiş {len(unprocessed_news)} haber bulundu")
                
            return unprocessed_news
            
        except Exception as e:
            logger.error(f"İşlenmemiş haberleri çekerken hata: {e}")
            return []
            
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
