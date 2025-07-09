"""
Persistence Manager Module

Bu modül, zenginleştirilmiş haber verilerini PostgreSQL veritabanına kaydetmeye
yarayan PersistenceManager sınıfını içerir.
"""

import logging
import psycopg2
import psycopg2.pool
import psycopg2.extras
from psycopg2.extras import execute_values
import pgvector.psycopg2
import numpy as np
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
            
    def fetch_news_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """
        Belirtilen ID'ye sahip haberin temel detaylarını getirir.
        
        Args:
            news_id: Haber ID'si
            
        Returns:
            Optional[Dict]: Haber detayları veya None (haber bulunamazsa)
        """
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarını kullan
                query = """
                SELECT id, title, url, publication_date, source, fetched_at
                FROM news
                WHERE id = %s
                """
                
                cur.execute(query, (news_id,))
                news = cur.fetchone()
                
                if news:
                    return dict(news)
                else:
                    logger.warning(f"Haber bulunamadı: ID={news_id}")
                    return None
        except Exception as e:
            logger.error(f"Haber çekilirken hata (ID={news_id}): {e}")
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)
                
    def fetch_news_by_ids(self, news_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Belirtilen ID'lere sahip haberlerin tüm detaylarını (temel bilgiler + zenginleştirilmiş veri) getirir.
        Bu metod, pipeline'da RAG adımı için gerekli tüm veriyi (entities, embedding_vector vb.) içerir.
        Verileri news, article_entities ve entities tablolarından birleştirerek tek bir sorguyla verimli şekilde çeker.
        
        V1__Create_AI_Pipeline_Tables.sql ve V2__Add_Embedding_Vector_To_News.sql migrasyonlarında
        tanımlanan şema yapısına göre hazırlanmıştır.
        
        Args:
            news_ids: Haber ID'leri listesi
            
        Returns:
            List[Dict]: Haber detayları listesi. Bulunamayan haberler listeye dahil edilmez.
        """
        if not news_ids:
            logger.warning("fetch_news_by_ids için boş ID listesi verildi")
            return []
            
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Her ID için bir yer tutucu (%s) oluştur
                placeholders = ','.join(['%s'] * len(news_ids))
                
                # V1__Create_AI_Pipeline_Tables.sql migrasyonuna göre tablo ve sütun adlarını kullan
                query = f"""
                SELECT 
                    n.id, 
                    n.title, 
                    n.url, 
                    n.publication_date, 
                    n.source,
                    n.fetched_at,
                    n.embedding_vector,
                    COALESCE(json_agg(
                        DISTINCT jsonb_build_object(
                            'name', e.name, 
                            'type', e.type,
                            'canonical_id', e.canonical_id
                        ) 
                        FILTER (WHERE e.id IS NOT NULL)
                    ), '[]'::json) as entities
                FROM 
                    news n
                LEFT JOIN 
                    article_entities ae ON n.id = ae.news_id
                LEFT JOIN 
                    entities e ON ae.entity_id = e.id
                WHERE 
                    n.id IN ({placeholders})
                GROUP BY 
                    n.id
                """
                
                cur.execute(query, news_ids)
                results = cur.fetchall()
                
                # Sonuçları dict listesine dönüştür ve entities alanını Python nesnesine çevir
                news_list = []
                for row in results:
                    news_item = dict(row)
                    
                    # entities alanını JSON'dan Python List'e dönüştür
                    # psycopg2 zaten JSON'u Python nesnesine çevirebiliyor olabilir,
                    # ancak bunu garanti altına alalım
                    if 'entities' in news_item and news_item['entities']:
                        if isinstance(news_item['entities'], str):
                            try:
                                import json
                                news_item['entities'] = json.loads(news_item['entities'])
                            except Exception as e:
                                logger.warning(f"JSON entities parse hatası: {e}")
                                news_item['entities'] = []
                    else:
                        news_item['entities'] = []
                        
                    news_list.append(news_item)
                
                logger.info(f"{len(news_list)}/{len(news_ids)} haber başarıyla getirildi")
                return news_list
                
        except Exception as e:
            logger.error(f"{len(news_ids)} haber çekilirken hata: {e}")
            return []
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
    

    
    def fetch_entities_by_news_id(self, news_id: int) -> List[Dict[str, Any]]:
        """
        Belirtilen habere ait varlıkları getirir.
        
        Args:
            news_id: Haber ID'si
            
        Returns:
            List[Dict]: Haberin varlıklarını içeren liste
        """
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarına uygun sorgu
                # article_entities tablosu üzerinden entities tablosuna join kullanarak doğru verileri getir
                query = """
                SELECT e.id, e.name, e.type
                FROM article_entities ae
                JOIN entities e ON ae.entity_id = e.id
                WHERE ae.news_id = %s
                """
                
                cur.execute(query, (news_id,))
                entities = [dict(row) for row in cur.fetchall()]
                
                logger.info(f"{len(entities)} adet varlık alındı (news_id={news_id})")
                return entities
        except Exception as e:
            logger.error(f"Varlıklar çekilirken hata (news_id={news_id}): {e}")
            return []
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
            
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
                error_message if status == PROCESSING_PARTIAL_SUCCESS else None,
                enriched_item.get("event_type")
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
                    # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarını kullan
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
            error_message: Optional[str] = None,
            event_type: Optional[str] = None,
            surprise_score: Optional[float] = None
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
            event_type: Belirlenen olay türü
            surprise_score: Hesaplanan sürpriz skoru (0.0-1.0 arası)
        """
        with conn.cursor() as cur:
            # Dinamik olarak eklenecek alanları ve değerlerini belirle
            # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarını kullan
            insert_fields = ["news_id", "status", "embedding_model_version"]
            insert_values = [news_id, status, model_version]
            update_fields = ["status", "embedding_model_version"]
            update_values = [status, model_version]
            
            # Opsiyonel alanları ekle
            if error_message is not None:
                insert_fields.append("error_message")
                insert_values.append(error_message)
                update_fields.append("error_message")
                update_values.append(error_message)
                
            if event_type is not None:
                # Dikkat: event_type için veritabanında bir sütun olmayabilir.
                # Bu durumda V7__Add_Event_Type_To_Log.sql migration'ının çalıştırılmış olduğunu varsayıyoruz
                insert_fields.append("event_type") 
                insert_values.append(event_type)
                update_fields.append("event_type")
                update_values.append(event_type)
                
            if surprise_score is not None:
                insert_fields.append("surprise_score")
                insert_values.append(surprise_score)
                update_fields.append("surprise_score")
                update_values.append(surprise_score)
            
            # INSERT sorgusu oluştur
            fields_str = ", ".join(insert_fields)
            placeholders = ", ".join([r"%s"] * len(insert_values))
            
            # UPDATE sorgusu oluştur
            update_str = ", ".join([f"{field} = %s" for field in update_fields])
            
            # Tam sorgu
            query = f"""
                INSERT INTO ai_processing_log 
                ({fields_str})
                VALUES ({placeholders})
                ON CONFLICT (news_id) DO UPDATE
                SET {update_str}
            """
            
            # Tüm parametreleri birleştir
            all_params = insert_values + update_values
            
            # Sorguyu çalıştır
            cur.execute(query, all_params)
            
            # Gömme vektörü varsa news tablosunu güncelle
            # V2__Add_Embedding_Vector_To_News.sql'e göre embedding_vector sütunu news tablosundadır
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
                # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarına uygun sorgu
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
                # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki sütun adlarına uygun SQL sorgusu
                # news tablosundan id, url, title ve source sütunlarını çeker
                # ai_processing_log tablosunda status sütununu kontrol eder
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
                
    def fetch_processed_news(self, limit: int = 1000) -> List[Dict]:
        """
        İşlenmiş haberleri veritabanından çeker.
        
        Args:
            limit: Çekilecek maksimum haber sayısı
            
        Returns:
            List[Dict]: İşlenmiş haber listesi (id, embedding_vector, entities ve published_at içeren)
        """
        processed_news = []
        conn = None
        
        try:
            # Bağlantı havuzundan bir bağlantı al
            conn = self.conn_pool.getconn()
            pgvector.psycopg2.register_vector(conn)
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # İşlenmiş ve embedding_vector'ü olan haberleri çek
                cur.execute("""
                    SELECT n.id, n.embedding_vector, n.published_at
                    FROM news n
                    JOIN ai_processing_log l ON n.id = l.news_id
                    WHERE l.status = %s AND n.embedding_vector IS NOT NULL
                    LIMIT %s
                """, (PROCESSING_SUCCESS, limit))
                
                rows = cur.fetchall()
                news_dict = {row['id']: dict(row) for row in rows}
                
                # Hiç haber bulunamadıysa boş liste döndür
                if not news_dict:
                    return []
                
                # Haberler için varlıkları çek
                news_ids = list(news_dict.keys())
                placeholders = ', '.join(['%s'] * len(news_ids))
                
                cur.execute(f"""
                    SELECT ae.news_id, e.id, e.name, e.type
                    FROM article_entities ae
                    JOIN entities e ON ae.entity_id = e.id
                    WHERE ae.news_id IN ({placeholders})
                """, news_ids)
                
                # Haber başına varlıkları grupla
                for row in cur.fetchall():
                    news_id = row['news_id']
                    entity = {
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type']
                    }
                    
                    if 'entities' not in news_dict[news_id]:
                        news_dict[news_id]['entities'] = []
                        
                    news_dict[news_id]['entities'].append(entity)
                
                processed_news = list(news_dict.values())
                logger.info(f"{len(processed_news)} işlenmiş haber bulundu")
                
            return processed_news
            
        except Exception as e:
            logger.error(f"İşlenmiş haberleri çekerken hata: {e}")
            return []
            
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
                
    def save_graph_edges(self, edge_records: List[Dict]) -> bool:
        """
        Haberler arasındaki etkileşim skorlarını graph_edges tablosuna kaydeder.
        
        Args:
            edge_records: Kaydedilecek kenar kayıtları listesi.
                         Her kayıt şu alanları içermelidir:
                         - source_news_id: Kaynak haber ID'si
                         - target_news_id: Hedef haber ID'si
                         - semantic_score: Semantik benzerlik skoru (0-1)
                         - entity_score: Varlık benzerliği skoru (0-1)
                         - temporal_score: Zamansal yakınlık skoru (0-1)
                         - total_score: Toplam etkileşim skoru (0-1)
                         
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        if not edge_records:
            logger.warning("Kaydedilecek kenar kaydı bulunamadı")
            return False
            
        conn = None
        try:
            # Bağlantı havuzundan bir bağlantı al
            conn = self.conn_pool.getconn()
            
            with conn.cursor() as cur:
                # Verileri execute_values ile toplu ekleme için hazırla
                data_to_insert = [
                    (
                        rec['source_news_id'],
                        rec['target_news_id'],
                        rec['semantic_score'],
                        rec['entity_score'],
                        rec['temporal_score'],
                        rec['total_score']
                    ) for rec in edge_records
                ]
                
                # execute_values ile toplu ekleme/güncelleme yap
                execute_values(
                    cur,
                    """
                    INSERT INTO graph_edges 
                    (source_news_id, target_news_id, semantic_score, entity_score, temporal_score, total_score)
                    VALUES %s
                    ON CONFLICT (source_news_id, target_news_id) DO UPDATE SET
                        semantic_score = EXCLUDED.semantic_score,
                        entity_score = EXCLUDED.entity_score,
                        temporal_score = EXCLUDED.temporal_score,
                        total_score = EXCLUDED.total_score,
                        updated_at = NOW()
                    """,
                    data_to_insert
                )
                
                # İşlemi onayla
                conn.commit()
                
                logger.info(f"{len(edge_records)} kenar kaydı başarıyla graph_edges tablosuna eklendi/güncellendi")
                return True
                
        except Exception as e:
            if conn:
                # Hata durumunda rollback yap
                conn.rollback()
            logger.error(f"Graph edges kaydederken hata: {e}")
            return False
            
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)

    def fetch_similar_stories_by_vector(self, vector: np.ndarray, k: int = 3) -> List[Dict[str, Any]]:
        """
        Verilen vektöre anlamsal olarak en benzer k adet hikayeyi veritabanından getirir.
        Bu metod, pgvector'un kosinüs mesafesi operatörünü (<->) kullanarak ANN araması yapar.
        
        Args:
            vector: Sorgulanacak hikaye vektörü (numpy.ndarray)
            k: Dönülecek maksimum benzer hikaye sayısı
            
        Returns:
            List[Dict]: En benzer k adet hikayenin detaylarını içeren liste
        """
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            # pgvector eklentisini kaydet
            pgvector.psycopg2.register_vector(conn)
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Vektörü PostgreSQL'in anlayacağı formata dönüştür
                pg_vector = list(vector)
                
                # Kosinüs mesafesi operatörü (<->) kullanarak sorgu yap
                # V1__Create_AI_Pipeline_Tables.sql migrasyonundaki gerçek sütun adlarına uygun sorgu
                query = """
                SELECT 
                    id as story_id, 
                    story_title, 
                    story_essence_text,
                    generated_at,
                    last_update_date,
                    story_embedding_vector <-> %s AS semantic_distance
                FROM analyzed_stories
                WHERE is_active = true
                ORDER BY semantic_distance
                LIMIT %s
                """
                
                cur.execute(query, (pg_vector, k))
                similar_stories = [dict(row) for row in cur.fetchall()]
                logger.info(f"{len(similar_stories)} benzer hikaye bulundu")
                
                return similar_stories
                
        except Exception as e:
            logger.error(f"Benzer hikayeleri sorgularken hata: {e}")
            return []
            
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
    
    def find_economic_events_by_date_range_and_keywords(self, start_date: date, end_date: date, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Belirli bir tarih aralığındaki ve belirli anahtar kelimeleri içeren ekonomik olayları getirir.
        
        V9__Create_Economic_Events.sql migrasyonunda tanımlanan şema yapısına göre hazırlanmıştır.
        
        Args:
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            keywords: Olay adında aranacak anahtar kelimeler listesi
            
        Returns:
            List[Dict]: Belirli tarih aralığında ve anahtar kelimeleri içeren ekonomik olaylar listesi
        """
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Anahtar kelimeler için ILIKE sorguları oluştur
                keyword_conditions = []
                query_params = [start_date, end_date]
                
                for keyword in keywords:
                    keyword_conditions.append("event_name ILIKE %s")
                    query_params.append(f'%{keyword}%')
                
                # Keyword koşullarını OR ile birleştir
                keyword_condition = " OR ".join(keyword_conditions) if keyword_conditions else "1=1"
                
                # V9 migrasyonunda tanımlanan gerçek sütun adlarını kullan
                query = f"""
                SELECT 
                    id, event_name, country, event_time, actual_value, forecast_value, 
                    previous_value, impact, unit, created_at, updated_at
                FROM economic_events
                WHERE event_time BETWEEN %s AND %s
                AND ({keyword_condition})
                ORDER BY event_time DESC
                """
                
                cur.execute(query, query_params)
                events = [dict(row) for row in cur.fetchall()]
                logger.info(f"{len(events)} adet ekonomik olay bulundu ({start_date} - {end_date})")
                
                # Geriye dönük uyumluluk için sütun isimlerini eski kodla uyumlu hale getir
                for event in events:
                    # Eski kodların event_date beklediği yerlerde kullanabilmesi için
                    if 'event_time' in event and 'event_date' not in event:
                        event['event_date'] = event['event_time']
                    # Eski kodların significance_score beklediği yerlerde kullanabilmesi için
                    if 'impact' in event and 'significance_score' not in event:
                        event['significance_score'] = event['impact']
                
                return events
        except Exception as e:
            logger.error(f"Ekonomik olayları sorgularken hata: {e}")
            return []
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
    
    def fetch_graph_edges(self, run_date: date = None, interaction_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Belirli bir tarih için eşik değerini aşan tüm etkileşim kenarlarını getirir.
        
        Args:
            run_date: Etkileşim kenarlarının ait olduğu tarih (None ise bugünün tarihi kullanılır)
            interaction_threshold: Minimum etkileşim skoru eşiği
            
        Returns:
            List[Dict]: Her kenar için kaynak ve hedef haber ID'lerini ve etkileşim skorlarını içeren sözlüklerden oluşan liste
        """
        if run_date is None:
            run_date = datetime.now().date()
        
        conn = None
        try:
            # Veritabanı bağlantısını havuzdan al
            conn = self.conn_pool.getconn()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                query = """
                SELECT 
                    source_news_id, target_news_id, semantic_score,
                    entity_score, temporal_score, total_interaction_score, run_date
                FROM graph_edges
                WHERE run_date = %s AND total_interaction_score >= %s
                ORDER BY total_interaction_score DESC
                """
                
                cur.execute(query, (run_date, interaction_threshold))
                edges = [dict(row) for row in cur.fetchall()]
                logger.info(f"{len(edges)} adet etkileşim kenarı alındı. (run_date={run_date}, threshold={interaction_threshold})")
                
                return edges
        except Exception as e:
            logger.error(f"Etkileşim kenarlarını çekerken hata: {e}")
            return []
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
                
    def save_story(self, story_data: Dict[str, Any]) -> Optional[int]:
        """
        Zenginleştirilmiş hikaye verilerini analyzed_stories tablosuna kaydeder.
        
        V1__Create_AI_Pipeline_Tables.sql, V4__Add_Story_Tracking.sql ve 
        V8__Add_Affected_Assets_To_Stories.sql migrasyonlarında tanımlanan şema yapısına 
        göre hazırlanmıştır.
        
        Args:
            story_data: Hikaye verileri şu alanları içermelidir:
                - news_ids: Hikayedeki haberlerin ID listesi
                - label: Hikaye için üretilen etiket (story_title olarak kaydedilir)
                - rationale: Etiket için üretilen gerekçe (connection_rationale olarak kaydedilir)
                - analysis_summary: Hikaye analiz özeti
                - story_essence_text: Hikayenin özü
                - story_context_snippets: Hikaye için bağlam parçaları listesi
                - story_embedding_vector: Hikaye için temsil vektörü
                - affected_assets: Etkilenen finansal varlıklar listesi (opsiyonel)
                
        Returns:
            Optional[int]: Oluşturulan hikaye kaydının ID'si, işlem başarısız olursa None
        """
        if not story_data.get("news_ids") or not story_data.get("label"):
            logger.error("Geçersiz hikaye verisi: news_ids ve label zorunlu alanlarıdır")
            return None
            
        conn = None
        try:
            # Girdileri hazırla
            news_ids = story_data.get("news_ids", [])
            story_title = story_data.get("label")
            analysis_summary = story_data.get("analysis_summary", "")
            connection_rationale = story_data.get("rationale", "")
            story_essence_text = story_data.get("story_essence_text")
            story_context_snippets = story_data.get("story_context_snippets")
            story_embedding_vector = story_data.get("story_embedding_vector")
            affected_assets = story_data.get("affected_assets")  # V8 migrasyonunda eklenen sütun
            
            # Veritabanına kaydet
            conn = self.conn_pool.getconn()
            with conn.cursor() as cursor:
                # V1, V4 ve V8 migrasyonlarında tanımlanan gerçek sütun adlarını kullan
                query = """
                INSERT INTO analyzed_stories 
                (story_title, analysis_summary, connection_rationale, story_essence_text, 
                 story_context_snippets, story_embedding_vector, is_active, last_update_date,
                 affected_assets)
                VALUES (%s, %s, %s, %s, %s, %s, true, NOW(), %s)
                RETURNING id
                """
                
                cursor.execute(
                    query, 
                    (story_title, analysis_summary, connection_rationale, story_essence_text, 
                     story_context_snippets, story_embedding_vector, affected_assets)
                )
                
                # Dönen ID'yi al
                story_id = cursor.fetchone()[0]
                conn.commit()
                
                # Hikaye-Haber ilişkisini kaydet
                if story_id and news_ids:
                    self._save_story_news_links(story_id, news_ids, conn)
                
                logger.info(f"Yeni hikaye kaydedildi: ID={story_id}, story_title='{story_title}'")
                return story_id
                
        except Exception as e:
            logger.error(f"Hikaye kaydederken hata: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self.conn_pool.putconn(conn)
                
    def _save_story_news_links(self, story_id: int, news_ids: List[int], conn: Optional[psycopg2.extensions.connection] = None) -> bool:
        """
        Hikaye ve haberler arasındaki ilişkileri story_news_link tablosuna kaydeder.
        
        Args:
            story_id: Hikaye ID'si
            news_ids: Haber ID'leri listesi
            conn: Aktif veritabanı bağlantısı (isteğe bağlı)
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if not story_id or not news_ids:
            logger.error("Geçersiz story_id veya boş news_ids listesi")
            return False
            
        close_conn = False
        if conn is None:
            conn = self.conn_pool.getconn()
            close_conn = True
            
        try:
            with conn.cursor() as cursor:
                # Çoklu değer ekleme için VALUES kısmını oluştur
                values_list = [(story_id, news_id) for news_id in news_ids]
                args_str = ','.join(cursor.mogrify("(%s,%s)", val).decode('utf-8') for val in values_list)
                
                # V1__Create_AI_Pipeline_Tables.sql'de tanımlanan story_news_link tablosuna kaydet
                query = f"""
                INSERT INTO story_news_link (story_id, news_id)
                VALUES {args_str}
                ON CONFLICT (story_id, news_id) DO NOTHING
                """
                
                cursor.execute(query)
                conn.commit()
                
                logger.info(f"Hikaye-Haber ilişkileri kaydedildi: story_id={story_id}, {len(news_ids)} haber")
                return True
                
        except Exception as e:
            logger.error(f"Hikaye-Haber ilişkilerini kaydederken hata: {e}")
            conn.rollback()
            return False
        finally:
            if close_conn and conn:
                self.conn_pool.putconn(conn)
    def save_story_relationship(self, source_story_id: int, target_story_id: int, relationship_type: str = "EVOLVED_FROM", created_by: str = "PipelineOrchestrator") -> bool:
        """
        İki hikaye arasındaki ilişkiyi story_relationships tablosuna kaydeder.
        
        Args:
            source_story_id: Kaynak (yeni) hikaye ID'si
            target_story_id: Hedef (eski/ebeveyn) hikaye ID'si
            relationship_type: İlişki tipi (ör. "EVOLVED_FROM")
            created_by: İlişkiyi oluşturan bileşen/kullanıcı
            
        Returns:
            bool: İşlem başarılı olduysa True, değilse False
        """
        if not source_story_id or not target_story_id:
            logger.error("Geçersiz ilişki verisi: source_story_id ve target_story_id zorunlu alanlardır")
            return False
            
        conn = None
        try:
            conn = self.conn_pool.getconn()
            with conn.cursor() as cursor:
                # İlişkiyi kaydet
                query = """
                INSERT INTO story_relationships 
                (source_story_id, target_story_id, relationship_type, is_active, created_by, created_at)
                VALUES (%s, %s, %s, true, %s, NOW())
                ON CONFLICT (source_story_id, target_story_id, relationship_type) 
                DO NOTHING
                """
                
                cursor.execute(query, (source_story_id, target_story_id, relationship_type, created_by))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Hikaye ilişkisi kaydedildi: {source_story_id} -> {target_story_id}, tip='{relationship_type}'")
                    return True
                else:
                    logger.warning(f"Bu ilişki zaten mevcut veya eklenemedi: {source_story_id} -> {target_story_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Hikaye ilişkisi kaydederken hata: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.conn_pool.putconn(conn)
    def save_economic_events(self, events_data: List[Dict[str, Any]]) -> bool:
        """
        Ekonomik olayları veritabanına kaydeder.
        
        V9__Create_Economic_Events.sql migrasyonunda tanımlanan şema yapısına göre hazırlanmıştır.
        
        Args:
            events_data: Kaydedilecek ekonomik olay verileri.
                           Her kayıt şu alanları içermelidir:
                           - event_name: Olayın adı
                           - event_time: Olayın tarihi ve saati (datetime)
                           - actual_value: Gerçekleşen değer (opsiyonel)
                           - forecast_value: Öngörülen değer (opsiyonel)
                           - previous_value: Önceki değer (opsiyonel)
                           - country: Ülke adı
                           - impact: Önem seviyesi [Low, Medium, High]
                           - unit: Değerin birimi
                           
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        if not events_data:
            logger.warning("Kaydedilecek ekonomik olay bulunamadı")
            return False
            
        conn = None
        try:
            # Bağlantıyı havuzdan al
            conn = self.conn_pool.getconn()
            
            with conn.cursor() as cur:
                # Verileri execute_values ile toplu ekleme için hazırla
                data_to_insert = []
                
                for event in events_data:
                    # Zorunlu alanları kontrol et
                    # Geriye dönük uyumluluk için hem event_time hem de event_date kontrolü yap
                    event_time = event.get("event_time") or event.get("event_date")
                    if not event.get("event_name") or not event_time:
                        logger.warning("event_name ve event_time zorunlu alanlar eksik, olay atlanıyor")
                        continue
                        
                    # impact için geriye dönük uyumluluk
                    impact = event.get("impact") or event.get("significance_score")
                    # unit için geriye dönük uyumluluk
                    unit = event.get("unit") or event.get("measurement_unit")
                        
                    # Veriyi hazırla - V9 migrasyonundaki sütun adlarına uygun şekilde
                    data_to_insert.append((
                        event.get("event_name"),
                        event.get("country", ""),  # country zorunlu alan
                        event_time,
                        event.get("actual_value"),
                        event.get("forecast_value"),
                        event.get("previous_value"),
                        impact,
                        unit,
                        datetime.now(),  # created_at
                        datetime.now()   # updated_at
                    ))
                
                if not data_to_insert:
                    logger.warning("Geçerli olay verisi bulunamadı")
                    return False
                
                # execute_values ile toplu ekleme/güncelleme yap
                # V9 migrasyonuna göre güncellenmiş sütun adlarını kullan
                execute_values(
                    cur,
                    """
                    INSERT INTO economic_events 
                    (event_name, country, event_time, actual_value, forecast_value, 
                     previous_value, impact, unit, created_at, updated_at)
                    VALUES %s
                    ON CONFLICT (event_name, country, event_time) DO UPDATE SET
                        actual_value = EXCLUDED.actual_value,
                        forecast_value = EXCLUDED.forecast_value,
                        previous_value = EXCLUDED.previous_value,
                        impact = EXCLUDED.impact,
                        unit = EXCLUDED.unit,
                        updated_at = NOW()
                    """,
                    data_to_insert
                )
                
                # İşlemi onayla
                conn.commit()
                
                logger.info(f"{len(data_to_insert)} ekonomik olay başarıyla economic_events tablosuna eklendi/güncellendi")
                return True
                
        except Exception as e:
            if conn:
                # Hata durumunda rollback yap
                conn.rollback()
            logger.error(f"Ekonomik olayları kaydederken hata: {e}")
            return False
            
        finally:
            # Bağlantıyı havuza geri ver
            if conn:
                self.conn_pool.putconn(conn)
