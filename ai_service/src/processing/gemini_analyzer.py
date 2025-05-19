import logging
import json
from typing import List, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.schemas import GeminiGroupResponseSchema, AnalyzedStorySchema
from src.core.config import settings

# Logger oluştur
logger = logging.getLogger(__name__)


def group_news_stories_with_gemini(news_batch_to_group: List[Dict], api_key: str) -> Optional[List[Dict]]:
    """
    Verilen haber listesini Gemini 1.5 Flash API'sini kullanarak anlamlı haber gruplarına ayırır.
    
    Args:
        news_batch_to_group: İşlenecek haberlerin listesi. Her haber şu alanları içermelidir:
                              {id, title, extracted_keywords, content}
        api_key: Gemini API anahtarı
        
    Returns:
        Başarılı olursa, her biri {"group_label": str, "related_news_ids": List[str]} içeren
        bir dict listesi. Başarısız olursa None.
    """
    if not news_batch_to_group:
        logger.warning("Gruplanacak haber listesi boş")
        return []
    
    if not api_key:
        logger.error("Gemini API anahtarı bulunamadı")
        return None
    
    # Haber listesinin boyutunu logla
    logger.info(f"Gemini API ile {len(news_batch_to_group)} haber gruplanıyor...")
    
    try:
        # Gemini API'yi yapılandır
        genai.configure(api_key=api_key)
        
        # Gemini modelini başlat
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings=[
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                }
            ]
        )
        
        # Haberleri JSON string'ine dönüştür
        news_json = json.dumps(news_batch_to_group, ensure_ascii=False, indent=2)
        
        # Örnek amaçlı çıktıyı göster
        example_output = [
            {
                "group_label": "Ekonomi: Enflasyon ve Faiz Oranları",
                "related_news_ids": ["1", "3", "7"]
            },
            {
                "group_label": "Teknoloji: Yapay Zeka Gelişmeleri",
                "related_news_ids": ["2", "5"]
            }
        ]
        example_output_json = json.dumps(example_output, ensure_ascii=False, indent=2)
        
        # Prompt oluştur - gelişen hikayeler için detaylı yönergeler ve örnek çıktı formatı içerir
        
        prompt = f"""
        # GÖREV TANIMI: GELİŞEN HİKAYELER İÇİN HABER GRUPLAMA

        Sen, farklı finansal, politik, teknolojik ve küresel olaylar arasındaki görünmeyen bağlantıları, zincirleme reaksiyonları ve ortak üst temaları tespit etme konusunda uzmanlaşmış, son derece deneyimli bir stratejik analiz ve araştırma şefisin. Görevin, aşağıda JSON formatında sunulan haber makalelerini (her biri `id`, `title`, `extracted_keywords` ve `content` içerir) derinlemesine inceleyerek, **yüzeyde farklı ve bağımsız gibi görünen olaylar arasında anlamlı, çapraz tematik veya potansiyel nedensel ilişkiler kuran "gelişen hikaye" grupları oluşturmaktır.**

        ## TEMEL PRENSİPLER VE İSTENMEYENLER:
        1.  **FARKLI OLAYLAR ARASI KÖPRÜLER:** Odak noktan, **KESİNLİKLE** sadece aynı olayı farklı kaynaklardan bildiren veya birbirinin kopyası gibi duran haberleri bir araya getirmek DEĞİLDİR. Bunun yerine, bir olayın başka bir alakasız gibi görünen olayı nasıl etkilediğini, tetiklediğini veya onunla nasıl daha büyük bir resmin parçası haline geldiğini gösteren gruplar oluşturmalısın. Örneğin, bir jeopolitik gelişmenin belirli bir emtia fiyatına etkisi ve bunun da bir sektördeki şirketlerin performansına yansıması gibi zincirleme etkileri ara.
        2.  **DERİN BAĞLANTILAR:** Sadece birkaç ortak anahtar kelimeye dayalı yüzeysel gruplamalar yapma. Haberlerin içerikleri arasında mantıksal bir akış, potansiyel bir etki mekanizması veya güçlü bir ortak tema olmalı.
        3.  **GRUP BÜYÜKLÜĞÜ:** Oluşturacağın **her grup MUTLAKA en az 2 haber içermelidir.** Tek haberden oluşan gruplar kabul edilmeyecektir.
        4.  **GRUP SAYISI:** Spesifik bir maksimum grup sayısı hedefleme. O günkü haber setinden gerçekten anlamlı, birbirinden belirgin şekilde ayrışan ve güçlü bağlantılara sahip **ana gelişen hikayeleri veya temaları** belirle. Eğer o gün çok bariz çapraz ilişkisel temalar yoksa, az sayıda grup üretmen (hatta hiç üretmemen) daha iyidir. Kalite, nicelikten önemlidir.

        ## BEKLENEN DÜŞÜNME VE ANALİZ ŞEKLİ (ÖRNEK AKIL YÜRÜTME):
        *   "Bir teknoloji şirketinin Ar-Ge bütçesini rekor seviyede artırdığına dair bir haber (ID: tech01), bir ülkenin yüksek nitelikli mühendisler için yeni bir vize programı başlattığı haberiyle (ID: gov05) ve belirli bir endüstride otomasyonun hızla yayılacağına dair bir analistle yapılan röportajla (ID: econ03) nasıl birleşebilir? Belki de tema 'Teknolojik İnovasyon ve Yetenek Yarışının Ekonomik Etkileri'dir."
        *   "Ortadoğu'da artan bir askeri gerginlik haberi (ID: geo07) ile küresel petrol sevkiyatlarında sigorta primlerinin yükseldiğine dair bir piyasa haberi (ID: market02) ve bir havayolu şirketinin artan yakıt maliyetleri nedeniyle kar marjının düştüğünü açıkladığı bir haber (ID: biz04) arasında 'Jeopolitik Risklerin Enerji Maliyetleri ve Taşımacılık Sektörüne Yansıması' gibi bir hikaye oluşabilir."

        ## ANALİZ EDİLECEK HABERLER (JSON Formatında):
        ```json
        {news_json}
        ```

        SENDEN İSTENEN ÇIKTI:
        Lütfen analizinin sonucunu, KESİNLİKLE aşağıdaki JSON formatında bir liste olarak ver. Bu listenin her bir elemanı, belirlediğin bir "gelişen hikaye" grubunu temsil etmelidir. Yanıtının başında veya sonunda kesinlikle başka hiçbir metin, açıklama veya giriş/sonuç cümlesi OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki listeyi döndür.
        ```json
        {example_output_json}
        ```

        Eğer verilen haberler arasında yukarıdaki prensiplere uygun, en az iki haber içeren ve farklı olaylar arasında anlamlı bağlantılar kuran hiçbir grup oluşturulamıyorsa, boş bir liste [] döndür.
        """
        
        # Gemini API'ye isteği gönder
        response = model.generate_content(prompt)
        
        # Yanıtı işle
        result_text = response.text.strip()
        
        # Yanıttan JSON yüklemeye çalış
        # Bazen Gemini kod blokları içinde yanıt döndürebilir (```json ... ```) 
        # veya ekstra metin ekleyebilir, bunları temizleyelim
        result_text = clean_gemini_response(result_text)
        
        # JSON'a çözme
        try:
            result_data = json.loads(result_text)
            
            # Doğrulama için Pydantic modelini kullan
            validated_data = validate_gemini_response(result_data)
            
            if validated_data:
                logger.info(f"Gemini API ile {len(validated_data)} haber grubu başarıyla oluşturuldu")
                return validated_data
            else:
                logger.error("Gemini yanıtı doğrulanamadı")
                return None
                
        except json.JSONDecodeError as json_err:
            logger.error(f"Gemini yanıtı JSON olarak ayrıştırılamadı: {json_err}")
            logger.debug(f"Alınan yanıt metni: {result_text}")
            return None
            
    except Exception as e:
        logger.error(f"Gemini API ile haber gruplama sırasında hata: {str(e)}")
        return None


def clean_gemini_response(response_text: str) -> str:
    """
    Gemini API'den gelen yanıtı temizler ve düzgün bir JSON metni elde eder.
    """
    # Kod bloklarını temizle (```json ve ``` işaretleri)
    if "```json" in response_text:
        # Kod bloğunun başlangıcını ve sonunu bul
        start_idx = response_text.find("```json") + 7  # "```json" ifadesinden sonraki indeks
        end_idx = response_text.find("```", start_idx)  # Sonraki "```" ifadesinin indeksi
        
        # Eğer sonraki "```" bulunursa, arasındaki metni al
        if end_idx != -1:
            return response_text[start_idx:end_idx].strip()
    
    # Eğer kod bloğu formatı yoksa, tüm metni döndür
    return response_text.strip()


def validate_gemini_response(response_data: List[Dict]) -> Optional[List[Dict]]:
    """
    Gemini API'den gelen yanıtı doğrular ve gerekirse düzeltir.
    """
    try:
        # Pydantic v2 ile doğrulama - RootModel kullanımı
        validated = GeminiGroupResponseSchema(root=response_data)
        return [item.model_dump() for item in validated.root]
    except Exception as e:
        logger.error(f"Gemini yanıtı doğrulanamadı: {str(e)}")
        
        # Manuel doğrulama ve düzeltme deneyelim
        valid_items = []
        for item in response_data:
            if isinstance(item, dict):
                group_label = item.get("group_label", "")
                related_news_ids = item.get("related_news_ids", [])
                
                # Temel doğrulama
                if group_label and isinstance(related_news_ids, list):
                    # related_news_ids içindeki tüm öğelerin string olduğundan emin ol
                    related_news_ids = [str(news_id) for news_id in related_news_ids]
                    valid_items.append({
                        "group_label": group_label,
                        "related_news_ids": related_news_ids
                    })
        
        if valid_items:
            logger.warning(f"Gemini yanıtı kısmen doğrulanıp düzeltildi. {len(valid_items)} geçerli grup bulundu.")
            return valid_items
        else:
            return None


def analyze_individual_story_group(
    news_group_details: List[Dict], 
    group_label_from_phase1: str, 
    api_key: str
) -> Optional[Dict]:
    """
    Aşama 1'de belirlenen bir haber grubu için detaylı analiz yapar (Aşama 2).
    
    Args:
        news_group_details: Analiz edilecek grupdaki haberler. Her haber şu alanları içermelidir:
                           {id, title, extracted_keywords, content}
        group_label_from_phase1: Aşama 1'de bu grup için üretilen etiket
        api_key: Gemini API anahtarı
        
    Returns:
        Başarılı olursa, {story_title, related_news_ids, analysis_summary, main_categories} 
        içeren bir dictionary. Başarısız olursa None.
    """
    if not news_group_details:
        logger.warning("Analiz edilecek haber grubu boş")
        return None
    
    if not api_key:
        logger.error("Gemini API anahtarı bulunamadı")
        return None
    
    # Gruptaki haber sayısını logla
    logger.info(f"Gemini API ile '{group_label_from_phase1}' başlıklı grupta {len(news_group_details)} haber analiz ediliyor...")
    
    try:
        # Gemini API'yi yapılandır
        genai.configure(api_key=api_key)
        
        # Gemini modelini başlat - Aşama 2 için daha yüksek token limiti
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4096,  # Aşama 2 için daha yüksek token limiti
            },
            safety_settings=[
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                }
            ]
        )
        
        # Haberleri JSON string'ine dönüştür
        news_json = json.dumps(news_group_details, ensure_ascii=False, indent=2)
        
        # Kategori listesi - Yalınlaştırılmış ana kategoriler
        categories = [
            "EKONOMİ", "PİYASALAR", "SİYASET", "JEOPOLİTİK", 
            "TEKNOLOJİ", "ENERJİ", "İKLİM"
        ]
        categories_str = ", ".join(categories)
        
        # Örnek çıktı oluştur
        example_output = {
            "story_title": "Merkez Bankası'nın Beklenmeyen Faiz Artırımı Piyasalarda Çalkantı Yarattı",
            "related_news_ids": [news_id for news in news_group_details[:3] if (news_id := news.get("id"))],
            "analysis_summary": "Merkez Bankası'nın bugün yaptığı beklenmedik faiz artırımı, enflasyonla mücadelede daha sert bir tutum sergileme niyetinin işareti olarak görüldü. Piyasalar bu karara sürpriz bir şekilde olumlu tepki gösterdi. Uzmanlar, bu hamlenin kısa vadede ekonomik büyümeyi yavaşlatabileceğini ancak uzun vadede daha sağlıklı bir enflasyon profiline yol açabileceğini düşünüyor.",
            "main_categories": ["EKONOMİ", "PİYASALAR"]
        }
        example_output_json = json.dumps(example_output, ensure_ascii=False, indent=2)
        
        # Prompt oluştur - detaylı analiz yönergeleri
        prompt = f"""
        # GÖREV TANIMI: HABER GRUBU İÇİN DERİNLEMESİNE ANALİZ, ÖZETLEME VE KATEGORİZASYON

        Sen, birbiriyle ilişkili olduğu önceden belirlenmiş bir grup finansal ve ilişkili haberi (başlık, çıkarılmış anahtar kelimeler ve tam metin içerir) analiz ederek, bu haberlerin ortak anlatısını, altta yatan neden-sonuç ilişkilerini, olaylar arası etkileşimlerini ve daha büyük resmi ortaya çıkaracak uzman bir araştırmacı ve analistsin. Amacın, sadece bireysel özetler değil, grubun bütününden doğan sinerjiyi yansıtan, kapsamlı ve içgörülü bir analiz üretmektir. Ürettigin analiz metninde kesinlikle harici veya dahili URL linkleri bulunmamalıdır.

        ## ANALİZ EDİLECEK HABER GRUBU:
        Bu haberler, daha önceki bir analizde "{group_label_from_phase1}" genel teması/etiketi altında birbiriyle bağlantılı olarak gruplandırılmıştır.

        Haberler (JSON formatında sana sunuluyor):
        ```json
        {news_json}
        ```

        DETAYLI GÖREVLERİN:
        Lütfen yukarıda verilen haber grubunu derinlemesine analiz ederek aşağıdaki anahtarları ve formatı içeren tek bir JSON objesi oluştur:
        story_title:
        Girişte verilen "{group_label_from_phase1}" etiketini dikkate alarak veya tamamen yeniden yorumlayarak, bu haber grubunun anlattığı ana bağlantılı hikayeyi veya gelişen temayı en iyi şekilde ifade eden, özgün, ilgi çekici ve analitik bir başlık oluştur. Bu başlık yaklaşık 5 ila 15 kelime arasında olmalıdır.
        related_news_ids:
        Bu analiz için sana verilen haberlerin orijinal id'lerini içeren listeyi değiştirmeden aynen buraya ekle.
        analysis_summary:
        Bu metin yaklaşık 350-700 kelime uzunluğunda olmalıdır.
        Giriş ve Ana Tema: Bu haber grubunun merkezindeki ana olay(lar)ı ve bunların oluşturduğu ortak/gelişen temayı veya ana hikayeyi net bir şekilde tanımlayarak başla.
        Haberler Arası Bağlantıların Detaylı Açıklaması: Gruptaki haberlerde anlatılan ana olayları, önemli verileri veya kilit argümanları belirgin bir şekilde ifade ederek (örn. "[Şirket adı]'nın açıkladığı rekor kar...", "X ülkesinin enerji politikalarındaki ani değişiklik...", "[Merkez Bankası Başkanı]'nın enflasyonla ilgili endişelerini dile getirmesi..." gibi), bu farklı olaylar veya bilgiler arasında nasıl bir ilişki, etkileşim, ardışıklık veya potansiyel nedensellik görüyorsun? Bir olay diğerini nasıl tetiklemiş, etkilemiş veya hangi ortak zemin üzerinde birleşmiş olabilir? Lütfen çıkarımlarını, verilen haber metinlerinden ve (varsa) extracted_keywords alanlarından spesifik pasajlara veya bilgilere atıfta bulunarak kanıtla ve detaylandır. Yüzeysel benzerliklerin ötesine geçerek altta yatan dinamikleri ve bağlantı noktalarını ortaya koy.
        Potansiyel Etkiler ve Öngörüler: Bu bağlantılı gelişmelerin veya ortaya çıkan temanın daha geniş anlamda (ekonomik, politik, sektörel, teknolojik vb.) olası kısa ve orta vadeli etkileri neler olabilir? Bu analizine dayanarak hangi potansiyel sonuçlar veya gelecekteki gelişmeler öngörülebilir? Bu bölümdeki çıkarımların spekulatif nitelikte olduğunu unutma.
        URL KULLANMA: Bu analiz metni içinde kesinlikle hiçbir URL linki kullanma.
        main_categories:
        Aşağıdaki önceden tanımlanmış ana kategori listesinden, bu analiz ettiğin genel hikayeye, bağlantılara ve potansiyel etkilere en uygun olan 1 veya 2 kategoriyi seçerek bir JSON listesi olarak ver:
        {categories}
        
        ÇIKTI FORMATI (JSON OBJESİ):
        Yanıtını KESİNLİKLE aşağıdaki JSON formatında tek bir obje olarak ver. Yanıtının başında veya sonunda kesinlikle başka hiçbir metin, açıklama veya giriş/sonuç cümlesi OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki objeyi döndür.

        ```json
        {example_output_json}
        ```

        ÖNEMLİ NOTLAR:
        Analizini sadece ve sadece sana verilen haber metinlerine, başlıklarına ve anahtar kelimelerine dayandır. Dışarıdan ek bilgi veya varsayım kullanma.
        Objektif, dengeli ve analitik bir dil kullanmaya özen göster.
        """
        
        # Gemini API'ye isteği gönder
        response = model.generate_content(prompt)
        
        # Yanıtı işle
        result_text = response.text.strip()
        
        # Yanıttan JSON yüklemeye çalış
        # Bazen Gemini kod blokları içinde yanıt döndürebilir (```json ... ```) 
        # veya ekstra metin ekleyebilir, bunları temizleyelim
        result_text = clean_gemini_response(result_text)
        
        # JSON'a çözme
        try:
            result_data = json.loads(result_text)
            
            # Doğrulama için Pydantic modelini kullan
            validated_data = validate_analyzed_story(result_data)
            
            if validated_data:
                logger.info(f"Grup '{group_label_from_phase1}' için detaylı analiz başarıyla tamamlandı")
                logger.info(f"Analiz başlığı: {validated_data['story_title']}")
                logger.info(f"Seçilen kategoriler: {', '.join(validated_data['main_categories'])}")
                return validated_data
            else:
                logger.error(f"Grup '{group_label_from_phase1}' için analiz yanıtı doğrulanamadı")
                return None
                
        except json.JSONDecodeError as json_err:
            logger.error(f"Gemini yanıtı JSON olarak ayrıştırılamadı: {json_err}")
            logger.debug(f"Alınan yanıt metni: {result_text}")
            return None
            
    except Exception as e:
        logger.error(f"Gemini API ile detaylı analiz sırasında hata: {str(e)}")
        return None


def validate_analyzed_story(response_data: Dict) -> Optional[Dict]:
    """
    Gemini API'den gelen detaylı analiz yanıtını doğrular ve gerekirse düzeltir.
    """
    try:
        # Pydantic v2 ile doğrulama
        validated = AnalyzedStorySchema(**response_data)
        return validated.model_dump()
    except Exception as e:
        logger.error(f"Gemini detaylı analiz yanıtı doğrulanamadı: {str(e)}")
        
        # Manuel doğrulama ve düzeltme deneyelim
        # Zorunlu alanları kontrol et ve varsa düzelt
        if not isinstance(response_data, dict):
            return None
            
        story_title = response_data.get("story_title", "")
        if not story_title:
            return None
            
        related_news_ids = response_data.get("related_news_ids", [])
        if not isinstance(related_news_ids, list) or not related_news_ids:
            return None
            
        # related_news_ids içindeki tüm öğelerin string olduğundan emin ol
        related_news_ids = [str(news_id) for news_id in related_news_ids]
        
        analysis_summary = response_data.get("analysis_summary", "")
        if not analysis_summary:
            return None
            
        main_categories = response_data.get("main_categories", [])
        if not isinstance(main_categories, list) or not main_categories:
            main_categories = ["GENEL"]  # Varsayılan kategori ekle
            
        # Tüm kategorileri büyük harfe çevir
        main_categories = [cat.upper() for cat in main_categories]
        
        # Valid story oluştur
        valid_story = {
            "story_title": story_title,
            "related_news_ids": related_news_ids,
            "analysis_summary": analysis_summary,
            "main_categories": main_categories
        }
        
        logger.warning("Gemini detaylı analiz yanıtı manuel olarak düzeltildi.")
        return valid_story