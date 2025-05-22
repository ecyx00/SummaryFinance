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
    Verilen haber listesini Gemini API'sini kullanarak anlamlı haber gruplarına ayırır.
    
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
        # GÖREV TANIMI: STRATEJİK FİNANSAL ANALİZ İLE ÖZGÜN VE BAĞLANTILI "GELİŞEN HİKAYE" GRUPLARI OLUŞTURMA

        Sen, küresel ekonomi, finansal piyasalar, şirket stratejileri, teknolojik kırılımlar ve jeopolitik dinamikler arasında karmaşık, genellikle gözden kaçan **nedensel ve tematik bağlantıları** tespit etme; farklı olaylar arasındaki **zincirleme reaksiyonları** ve altta yatan **makro temaları sentezleme** konusunda uzmanlaşmış, üst düzey bir **stratejik analiz ve araştırma direktörüsün.** Temel görevin, sinyali gürültüden ayırmak, yüzeysel benzerliklerin ötesine geçmek ve farklı bilgi parçacıklarından **bütüncül, içgörülü ve dinamik "gelişen hikayeler"** inşa etmektir.
        
        SANA VERİLEN GÖREV: Aşağıda JSON formatında sunulan bir dizi haber makalesini (her biri `id`, `title`, `extracted_keywords` ve `content` alanlarını içerir) derinlemesine inceleyeceksin. Bu inceleme sonucunda, ilk bakışta bağımsız veya alakasız gibi görünen olaylar arasında **anlamlı, disiplinlerarası, çapraz tematik ve/veya potansiyel nedensel ilişkiler** kuran, birbirinden belirgin şekilde ayrışan **"gelişen hikaye" grupları** oluşturman beklenmektedir. **Amacın, sadece aynı konuyu farklı kaynaklardan bildiren haberleri bir araya getirmek KESİNLİKLE DEĞİLDİR.**
        
        ## TEMEL PRENSİPLER VE KESİNLİKLE UYULMASI GEREKEN ÇIKTI KURALLARI:
        
        1.  **ÖZGÜN BAĞLANTILAR VE "GELİŞEN HİKAYE" ODAĞI (KRİTİK!):**
            *   **ASLA ve ASLA** sadece aynı olayı (örneğin, aynı şirket duyurusunu, aynı ekonomik veri açıklamasını veya aynı politik kararı) farklı kaynaklardan bildiren, birbirinin tekrarı olan veya içerik olarak çok benzer haberleri bir araya getirme. Bu tür "aynı konu" gruplamaları **KESİNLİKLE İSTENMEMEKTEDİR ve DEĞERSİZDİR.**
            *   Bunun yerine, **FARKLI OLAYLAR veya GELİŞMELER** içeren haberler arasında köprüler kur. Bir olayın, normalde ilgisiz görünen başka bir alandaki bir olayı nasıl etkilediğini, tetiklediğini, onunla nasıl birleşerek daha büyük ve yeni bir anlam katmanı oluşturduğunu veya daha geniş bir makro trendin birbirini etkileyen farklı parçaları olduğunu gösteren **özgün ve içgörülü** gruplar oluşturmalısın.
            *   Bir "gelişen hikaye", zaman içinde farklı unsurların bir araya gelmesiyle veya birbirini etkilemesiyle şekillenen bir anlatıdır.
        
        2.  **DERİN VE ANLAMLI İLİŞKİLER:**
            *   Yalnızca birkaç ortak anahtar kelimenin varlığına dayalı yüzeysel veya zorlama gruplamalar yapmaktan **KESİNLİKLE KAÇIN.**
            *   Grupladığın haberlerin içerikleri arasında somut, mantıksal bir akış, kanıtlanabilir veya güçlü bir şekilde çıkarımlanabilir bir etki mekanizması (A, B'yi etkiledi; C ve D aynı büyük trendin sonuçlarıdır vb.) veya birbirini tamamlayan/açıklayan güçlü bir ortak tema olmalıdır.
            *   "Bu haberler 'teknoloji' hakkında" gibi genel konu etiketleri bir grup oluşturmak için yeterli değildir; haberler arasında spesifik ve **dinamik bir ilişki** tanımlanmalıdır.
        
        3.  **MİNİMUM GRUP BÜYÜKLÜĞÜ VE GEÇERLİ GRUPLAR (ÇOK KRİTİK!):**
            *   Oluşturacağın her bir JSON objesindeki (yani her bir grup için) `related_news_ids` listesi **KESİNLİKLE ve İSTİSNASIZ olarak en az 2 (iki) farklı haber ID'si içermelidir.**
            *   Eğer birbiriyle güçlü bir şekilde ilişkili olduğunu düşündüğün, ancak sayısı 2'den az olan haberler varsa, bu haberleri herhangi bir gruba dahil **ETME**.
            *   Çıktı olarak vereceğin JSON listesinde, `related_news_ids` listesinde **sadece 1 (bir) haber ID'si bulunan HİÇBİR grup objesi OLMAMALIDIR.** Bu tür objeler geçersizdir ve yanıtında yer almamalıdır.
        
        4.  **GRUP SAYISI VE KALİTE ÖNCELİĞİ (ÇOK ÖNEMLİ! BU BÖLÜME DİKKAT ET!):**
            *   Belirli bir sayıda grup oluşturma zorunluluğun YOKTUR. Önceliğin, **gerçekten anlamlı, birbirinden net bir şekilde ayrışan, bariz ve güçlü iç bağlantılara sahip "gelişen hikayeler"** tespit etmektir.
            *   **HEDEFİN, GÜNLÜK OLARAK ORTALAMA 2 İLA 5 ADET ARASINDA, YÜKSEK KALİTELİ VE STRATEJİK ÖNEME SAHİP GRUP ÜRETMEKTİR.** Bu bir kesin sınır değildir, ancak kaliteyi korumak için bir referanstır. 10 veya daha fazla sayıda grup üretmek genellikle istenmeyen bir durumdur ve büyük ihtimalle zayıf bağlantılar içerir.
            *   Eğer o günkü haber seti içerisinde yukarıdaki katı kriterlere uyan, **gerçekten bariz, güçlü ve stratejik öneme sahip çapraz ilişkisel temalar** bu hedeflenen sayının (2-5) altında ise, sadece o kadarını üret. Gerekirse sadece 1-2 grup üret veya **hiç grup üretme.**
            *   **Kalite, nicelikten KESİNLİKLE daha önemlidir.** Anlamsız, zorlama, "olsa da olur" tarzı veya sadece yüzeysel konu benzerliğine dayanan gruplar oluşturmaktan **KESİNLİKLE KAÇIN.** Şüphede kaldığında, daha az sayıda ama daha kaliteli grup üretmek her zaman daha iyidir. Eğer güçlü bir "gelişen hikaye" göremiyorsan, grup oluşturma.
        
        5.  **GRUPLAMA ODAĞI:** Haberlerin konuları farklı olabilir (örn: biri enerji, diğeri jeopolitik), ancak aralarında bir "hikaye" oluşturacak bir **etkileşim, sonuç, nedensellik veya birbirini etkileyen ortak bir üst tema** olmalıdır.
        
        ## BEKLENEN DÜŞÜNME VE ANALİZ ŞEKLİ (OLUMLU VE OLUMSUZ ÖRNEKLERLE):
        
        ### OLUMLU GRUPLAMA ÖRNEKLERİ (İSTENEN DAVRANIŞ – FARKLI OLAYLAR ARASINDA ANLAMLI BAĞLANTI):
        
        *   **OLUMLU ÖRNEK 1 (Sektörel Etkileşim ve Tedarik Zinciri):**
            *   **Haberler (Özetlenmiş İçerik):**
                1.  (ID: tech01) "Dev çip üreticisi AlphaChips, yeni nesil işlemcilerinde beklenmedik üretim sorunları yaşıyor, teslimatlar gecikebilir."
                2.  (ID: auto05) "Önde gelen otomobil firması BetaMotors, AlphaChips'ten tedarik ettiği çiplerdeki aksama nedeniyle bu çeyrekteki elektrikli araç üretim hedefini %15 düşürdüğünü açıkladı."
                3.  (ID: econ03) "Ekonomist Dr. Z, küresel tedarik zincirlerindeki devam eden kırılganlıkların ve belirli kritik bileşenlerdeki darboğazların enflasyonist baskıyı artırdığını ve büyüme üzerinde risk oluşturduğunu belirtti."
            *   **Neden Olumlu?** Farklı sektörlerdeki (teknoloji, otomotiv) spesifik olayların birbirini (AlphaChips sorunu -> BetaMotors üretimi) ve genel ekonomiyi (tedarik zinciri kırılganlığı -> enflasyon/büyüme) nasıl etkilediğini gösteren, nedensel bağlar içeren bir "gelişen hikaye" oluşturuyor. `related_news_ids` en az 2 haber içeriyor.
            *   **Örnek Çıktı (Bu haberlere göre):**
                ```json
                [
                    {{
                        "group_label": "Çip Tedarik Sorunlarının Otomotiv Üretimine ve Ekonomik Büyümeye Etkileri",
                        "related_news_ids": ["tech01", "auto05", "econ03"]
                    }}
                ]
                ```
        
        *   **OLUMLU ÖRNEK 2 (Jeopolitik Gelişme ve Piyasa Reaksiyonu):**
            *   **Haberler (Özetlenmiş İçerik):**
                1.  (ID: geo07) "Petrol zengini Ruritania ülkesinde artan iç karışıklıklar ve hükümet karşıtı protestolar yayılıyor."
                2.  (ID: energy02) "Ruritania'daki siyasi belirsizlik nedeniyle ham petrol fiyatları son altı ayın en yüksek seviyesine çıktı."
                3.  (ID: biz04) "Uluslararası enerji şirketi GammaEnergy, Ruritania'daki operasyonlarını geçici olarak askıya almayı değerlendirdiğini duyurdu."
            *   **Neden Olumlu?** Jeopolitik bir olayın (iç karışıklık) doğrudan emtia piyasalarını (petrol fiyatları) ve uluslararası şirketlerin operasyonel kararlarını nasıl etkilediğini gösteren, farklı alanlar arası bir bağlantı kuruyor. `related_news_ids` en az 2 haber içeriyor.
            *   **Örnek Çıktı (Bu haberlere göre):**
                ```json
                [
                    {{
                        "group_label": "Ruritania'daki Siyasi İstikrarsızlığın Petrol Piyasalarına ve Enerji Şirketlerine Yansıması",
                        "related_news_ids": ["geo07", "energy02", "biz04"]
                    }}
                ]
                ```
        
        ### OLUMSUZ GRUPLAMA ÖRNEKLERİ (KESİNLİKLE İSTENMEYEN DAVRANIŞ – YAPMA!):
        
        *   **OLUMSUZ ÖRNEK 1 (Aynı Olayın Farklı Kaynaklardan Tekrarı - DEĞERSİZ):**
            *   **Haberler:**
                1.  (ID: comp01) "ABC Şirketi, 2025 ilk çeyrekte gelirlerinin %10 arttığını açıkladı." (Kaynak: Haber Ajansı X)
                2.  (ID: comp02) "ABC Şirketi'nden Güçlü Bilanço: Gelirler %10 Yükseldi." (Kaynak: Finans Gazetesi Y)
                3.  (ID: comp03) "Teknoloji Devi ABC, Yılın İlk Çeyreğinde %10 Gelir Artışı Kaydetti." (Kaynak: İş Dünyası Dergisi Z)
            *   **Neden Olumsuz?** Bu üç haber de **TAMAMEN AYNI OLAYI** (ABC şirketinin gelir artışı) bildiriyor. Aralarında farklı olayları birbirine bağlayan bir "gelişen hikaye" veya özgün bir etkileşim yok. Sadece aynı bilginin tekrarı. **Bu tür "aynı konu" gruplamaları KESİNLİKLE YAPMA!**
            *   **Bu Durumda Beklenen Davranış:** Eğer bu haberler arasında başka bir olayla (örneğin, bu gelir artışının bir rakip şirketin hisselerini nasıl etkilediği gibi) anlamlı bir etkileşim yoksa, bu haberler için bir grup OLUŞTURULMAMALIDIR.
        
        *   **OLUMSUZ ÖRNEK 2 (Tek Haberlik Grup - KURAL İHLALİ - DEĞERSİZ):**
            *   **Haberler:**
                1.  (ID: econ05) "Merkez Bankası Başkanı, enflasyonun yıl sonunda %5'in altına düşmesini beklediklerini açıkladı."
            *   **Neden Olumsuz?** `related_news_ids` listesinde sadece bir haber ID'si var. "MİNİMUM GRUP BÜYÜKLÜĞÜ" kuralına göre her grup **en az 2 haber içermelidir.** Tek haberden oluşan gruplar KESİNLİKLE kabul edilemez ve DEĞERSİZDİR.
            *   **Bu Durumda Beklenen Davranış:** Bu haber için bir grup OLUŞTURULMAMALIDIR.
        
        *   **OLUMSUZ ÖRNEK 3 (Yüzeysel Benzerlik, Dinamik Yok):**
            *   **Haberler:**
                1.  (ID: apple01) "Apple Yeni iPhone Modelini Tanıttı, Gelişmiş Kamera Özellikleri Dikkat Çekiyor."
                2.  (ID: samsung01) "Samsung, Katlanabilir Ekran Teknolojisine Sahip Yeni Galaxy Z Serisini Duyurdu."
                3.  (ID: google01) "Google, Pixel Telefonları İçin Yeni Bir Yapay Zeka Destekli Yazılım Güncellemesi Yayınladı."
            *   **Potansiyel Grup Etiketi (KÖTÜ):** "Yeni Akıllı Telefon Gelişmeleri"
            *   **Neden Olumsuz?** Bu haberler genel olarak "akıllı telefonlar" ile ilgili olsa da, aralarında spesifik bir etkileşim, birbirini tetikleyen bir olay zinciri veya ortak bir "gelişen hikaye" görünmüyor. Sadece aynı sektördeki farklı şirketlerin bağımsız duyuruları. Bu tür genel konu başlığı altında birleştirme İSTENMEMEKTEDİR. (Ancak, bu haberlere ek olarak "Tüketicilerin Akıllı Telefon Değiştirme Sıklığı Artıyor" veya "Çip Üreticileri Telefonlara Özel Yeni Nesil İşlemcileri Piyasaya Sürüyor" gibi bir haber olsaydı, o zaman daha anlamlı bir "gelişen hikaye" kurulabilirdi.)
        
        *   **OLUMSUZ ÖRNEK 4 (ÇOK FAZLA ZAYIF GRUP ÜRETME EĞİLİMİ - İSTENMİYOR):**
            *   **Durum:** Sana verilen 50 haber arasında belki 1-2 tane gerçekten güçlü "gelişen hikaye" potansiyeli var. Ancak sen, bu 50 haberden 10-12 farklı grup çıkarmaya çalışıyorsun. Bu grupların çoğu muhtemelen zayıf tematik benzerliklere, tesadüfi anahtar kelime örtüşmelerine dayanıyor veya yukarıdaki "Aynı Olayın Tekrarı" ya da "Yüzeysel Benzerlik" kategorilerine giriyor olacak.
            *   **Neden Olumsuz?** Amaç, her küçük olasılığı gruplamak değil, sadece en belirgin, en önemli ve en güçlü bağlantıları yakalamaktır. Çok fazla sayıda, düşük kaliteli grup üretmek, analizin değerini düşürür ve "sinyali gürültüye boğar".
            *   **Bu Durumda Beklenen Davranış:** Sadece en güçlü 2-3 (veya o günkü duruma göre belki 1 veya 4-5) bağlantıyı grup olarak sun. Geri kalan zayıf olasılıkları **gruplama.** Kaliteye odaklan, sayıya değil.
        
        ## ANALİZ EDİLECEK HABERLER (JSON Formatında):
        ```json
        {news_json}
        ```
        SENDEN İSTENEN ÇIKTI:
        Lütfen analizinin sonucunu, KESİNLİKLE aşağıdaki JSON formatında bir liste olarak ver. Bu listenin her bir elemanı, yukarıdaki prensipler doğrultusunda belirlediğin bir "gelişen hikaye" grubunu temsil eden bir JSON objesi olmalıdır.
        Her bir grup objesi şu iki anahtarı içermelidir:
         1. group_label: String. Bu gruptaki haberlerin oluşturduğu, yukarıda tanımlanan "gelişen hikaye"yi veya olaylar arasındaki dinamik bağlantıyı/etkileşimi yansıtan, kısa (tercihen 3-10 kelime), öz ve analitik bir etiket. Bu etiket, haberlerin basit bir konu özeti olmamalı, aralarındaki dinamiği, nedenselliği veya ortak sonucu ifade etmelidir.
         2. related_news_ids: List[String]. Bu "gelişen hikaye" grubunu oluşturan ve sana verilen haberlerin orijinal id'lerini içeren bir liste. Bu listeye sadece gerçekten bu hikayeyle güçlü, anlamlı ve yukarıdaki prensiplere uygun bir bağlantısı olan haberlerin ID'lerini ekle. Bu liste KESİNLİKLE en az 2 (iki) ID içermelidir.
        Çıktının tamamı bir JSON listesi olmalıdır. Yanıtının başında veya sonunda kesinlikle başka hiçbir metin, açıklama, selamlama, giriş/sonuç cümlesi veya markdown formatlaşması (```json gibi) OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki listeyi döndür.
        ÖRNEK ÇIKTI FORMATI:
        {example_output_json}
        
        Eğer verilen haberler arasında yukarıdaki katı prensiplere uygun, related_news_ids listesinde en az iki haber ID'si içeren ve farklı olaylar arasında anlamlı, derin ve içgörülü bağlantılar kuran hiçbir "gelişen hikaye" grubu oluşturamıyorsan, boş bir JSON listesi [] döndür.
        **UNUTMA: Az sayıda (hatta hiç) yüksek kaliteli grup, çok sayıda düşük kaliteli gruptan çok daha değerlidir.**
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
        # GÖREV TANIMI: UZMAN FİNANSAL ANALİST VE KÖŞE YAZARI GÖZÜYLE BÜTÜNCÜL HİKAYE VE ÖNGÖRÜ RAPORU OLUŞTURMA

        Sen, uluslararası saygın bir finans yayınında (örneğin The Economist, Wall Street Journal, Financial Times) çalışan, keskin zekalı, deneyimli bir **kıdemli finansal analist ve köşe yazarısın.** Temel uzmanlığın, görünüşte bağımsız gibi duran ekonomik, politik, teknolojik ve piyasa olayları arasındaki **derin ve genellikle gözden kaçan bağlantıları** tespit etmek, bu olaylardan **bütüncül ve anlamlı bir "gelişen hikaye"** sentezlemek ve bu senteze dayanarak **içgörülü, ileriye dönük stratejik değerlendirmeler ve öngörüler** sunmaktır. Amacın, okuyucularına sadece ne olduğunu değil, neden olduğunu, olayların birbirini nasıl etkilediğini ve bundan sonra ne olabileceğini düşündüren, **akıcı, analitik ve sofistike bir dille** yazılmış bir analiz sunmaktır. Ürettiğin analiz metninde kesinlikle harici veya dahili URL linkleri bulunmamalıdır.

        ## ANALİZ EDİLECEK HABER GRUBU:
        Bu haberler, daha önceki bir ön analizde "{group_label_from_phase1}" genel teması/etiketi altında birbiriyle bağlantılı olabileceği düşünülen bir seçkidir. Senin görevin, bu seçkiyi bir **köşe yazısı veya derinlemesine bir analiz raporu formatında** ele alarak, bu bağlantıyı daha da derinleştirmek, olayları bir hikayeye dönüştürmek ve stratejik çıkarımlar yapmaktır.

        Haberler (JSON formatında sana sunuluyor):
        ```json
        {news_json}
        ```
        DETAYLI GÖREVLERİN:
        Lütfen yukarıda verilen haber grubunu, bir kıdemli finansal analist ve köşe yazarı perspektifiyle derinlemesine analiz ederek aşağıdaki anahtarları ve formatı içeren tek bir JSON objesi oluştur:
        story_title:
        Bu haber grubunun anlattığı ana, gelişen ve bağlantılı hikayeyi en iyi şekilde ifade eden, bir köşe yazısı başlığına yakışır, özgün, ilgi çekici ve analitik bir başlık oluştur. Başlık, okuyucunun merakını cezbetmeli ve analizin ana fikrini yansıtmalıdır. Yaklaşık 5 ila 15 kelime arasında olmalıdır.
        related_news_ids:
        Bu analiz için sana verilen haberlerin orijinal id'lerini içeren listeyi değiştirmeden aynen buraya ekle.
        analysis_summary:
        Bu metin yaklaşık 350-700 kelime uzunluğunda olmalıdır ve aşağıdaki düşünce akışını izleyerek, farklı haberlerdeki bilgileri organik bir şekilde sentezleyen, tek ve akıcı bir anlatı oluşturmalıdır. Amacın, haberleri tek tek sıralamak veya özetlemek DEĞİLDİR. Bunun yerine, bu haberlerin işaret ettiği daha büyük resmi ve olaylar arasındaki dinamikleri ortaya koyan, yorum ve analiz içeren bir metin üretmektir:

        1.Giriş - Sahneyi Kurma ve Ana Temayı Sunma: Analizine, bu haber grubunun işaret ettiği merkezi temayı veya gelişen hikayeyi çarpıcı bir şekilde tanıtarak başla. Okuyucuya, neden bu haberlerin bir arada önemli olduğunu ve hangi daha büyük resmi anlamalarına yardımcı olacağını hissettir.
        2.Olayların Sentezlenmesi ve Dinamik Bağlantıların Örülmesi:
         -Gruptaki haberlerde öne çıkan kilit olayları, verileri veya önemli açıklamaları, birbirleriyle olan ilişkilerini, etkileşimlerini ve potansiyel neden-sonuç bağlantılarını vurgulayarak anlatına dahil et.
         -Farklı haberlerdeki bilgileri, bir olayın diğerini nasıl etkilediğini veya birbiriyle nasıl birleşerek yeni bir durum oluşturduğunu gösterecek şekilde birbirine ör. Örneğin, bir haberdeki politik bir kararın, başka bir haberdeki ekonomik bir veriyi nasıl etkilediğini veya bir teknolojik gelişmenin farklı sektörlerde nasıl yankı bulduğunu anlat.
         -Çıkarımlarını, verilen haber metinlerinden aldığın spesifik bilgilere dayandır, ancak bu bilgileri sadece aktarmak yerine yorumla, aralarındaki boşlukları mantıksal çıkarımlarla doldur ve sentezle.
        3.Analitik Değerlendirme ve Stratejik Öngörüler:
         -Ortaya koyduğun bu bütüncül hikaye ve olaylar arasındaki dinamik bağlantılar ışığında, bu gelişmelerin daha geniş anlamda (ekonomik, politik, sektörel, teknolojik vb.) olası kısa ve orta vadeli stratejik sonuçları ve nedensel etkileri neler olabilir?
         -Bu analizine dayanarak, hangi yeni trendler, riskler, fırsatlar veya potansiyel politika/şirket stratejisi değişiklikleri öngörülebilir? Spekulatif ama mantığa dayalı, okuyucuyu düşündüren ve ona bir perspektif sunan 2-3 önemli öngörüde bulun.
        4.URL KULLANMA: Bu analiz metni içinde kesinlikle hiçbir URL linki kullanma.
         main_categories:
         Aşağıdaki önceden tanımlanmış ana kategori listesinden, bu analiz ettiğin bütüncül 
         hikayeye, ortaya koyduğun bağlantılara ve öngörülerine en uygun olan 1 veya 2 
         kategoriyi seçerek bir JSON listesi olarak ver:
        {categories_str}

        ÇIKTI FORMATI (JSON OBJESİ):
        Yanıtını KESİNLİKLE aşağıdaki JSON formatında tek bir obje olarak ver. Yanıtının başında veya sonunda kesinlikle başka hiçbir metin, açıklama veya giriş/sonuç cümlesi OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki objeyi döndür.
        ÖRNEK ÇIKTI FORMATI İÇİN analysis_summary (İstenen Tarzda):

        {example_output_json}

        TERCİH EDİLEN ANLATIM ÜSLUBU VE KESİNLİKLE KAÇINILMASI GEREKENLER (analysis_summary için):
        Lütfen analysis_summary metnini, yukarıdaki ÖRNEK ÇIKTI FORMATI İÇİN analysis_summary metninde gösterilen tarza uygun olarak, bir kıdemli finansal analist ve köşe yazarı gibi oluştur:

        TERCİH EDİLEN YAKLAŞIMLAR (BUNLARI YAP):
        1. Hikayeleştirme ve Bütüncül Sentez: Ayrı haberleri özetlemek yerine, bu haberlerdeki kilit bilgileri alıp bunları birleştirerek, olaylar arasında mantıksal bir akış ve derinlemesine bağlantılar kuran tek, tutarlı ve analitik bir hikaye/anlatı oluştur. Amacın, okuyucuya "bu haberler bir araya geldiğinde hangi daha büyük ve anlamlı hikaye ortaya çıkıyor ve bunun sonuçları ne olabilir?" sorusunun cevabını vermektir.
        2. Olay Odaklı ve Dinamik Bağlantılar: Haberlerdeki bilgilere atıfta bulunurken, olayın kendisini, konusunu veya sonucunu tanımlayan ve diğer olaylarla nedensel veya tematik ilişkisini gösteren ifadeler kullan.
         -ÖRNEK (ÇOK İYİ): "X Bankası'nın sermaye artırımı kararı, sektördeki artan rekabet 
         koşulları ve Y düzenleyici kurumunun getirdiği yeni likidite gereksinimleri bağlamında 
         değerlendirilmelidir. Bu hamle, bankanın bilançosunu güçlendirmeyi hedeflerken, aynı 
         zamanda daha küçük ölçekli rakipleri üzerinde konsolidasyon baskısı yaratabilir."
        3. Akıcı ve Mantıksal Geçişler: Farklı olayları, argümanları veya çıkarımları birbirine bağlarken "bu nedenle", "bunun bir sonucu olarak", "bu gelişmeye paralel olarak", "diğer yandan", "ancak", "bununla birlikte", "nitekim", "söz konusu gelişmeler ışığında" gibi çeşitli ve anlamlı geçiş ifadeleri kullanarak neden-sonuç ilişkilerini, karşıtlıkları veya çıkarımları açıkça vurgula.
        4. Analitik Derinlik ve Stratejik Öngörü: Yüzeysel bir anlatımdan ziyade, olayların altında yatan dinamikleri, potansiyel sonuçlarını ve daha geniş stratejik etkileşimlerini sorgulayan, analitik ve öngörüye dayalı bir bakış açısı sun. "Bu durum, önümüzdeki çeyrekte Z sektöründe bir daralmaya işaret edebilir" veya "Bu politika değişikliği, A ve B ülkeleri arasındaki ticaret dengesini yeniden şekillendirme potansiyeli taşıyor" gibi somut ve düşündürücü çıkarımlar yap.

        KAÇINILMASI GEREKEN YAKLAŞIMLAR (BUNLARI KESİNLİKLE YAPMA):
        1. Haberleri Tek Tek Özetleme veya Paragraf Paragraf Sıralama:
         -ÖRNEK (ÇOK KÖTÜ - YAPMA): "İlk haberde, M&S'in siber saldırıdan dolayı 300 milyon 
         sterlin zarar ettiği belirtiliyor. CEO, sosyal mühendislik kullanıldığını söyledi. İkinci 
         haberde, müşterilerin deneyimleri soruluyor. Müşteri verilerinin çalınması riskinden 
         bahsediliyor. Üçüncü haberde ise Scattered Spider adlı hacker grubu ve fidye yazılımı 
         olasılığı inceleniyor."
         -NEDEN ÇOK KÖTÜ? Bu, haberlerin bir listesidir, aralarında bir sentez, hikaye veya 
         derinlemesine bir bağlantı kurulmamıştır. Senden beklenen bu DEĞİLDİR.
        2. "Bu haberde...", "Birinci haberde...", "Bu haber grubu..." Gibi Mekanik ve Yönlendirici İfadeler: Bu tür ifadeler metni bir rapor veya ödev gibi gösterir, akıcı bir köşe yazısı veya analiz gibi değil.
        3. Yüzeysel "Ortak Nokta" Tespiti: Haberleri ayrı ayrı anlattıktan sonra sonunda çok genel bir "bu haberlerin ortak noktası siber güvenliktir" demek yerine, bu ortak temayı veya gelişen hikayeyi analizin tamamına organik bir şekilde yedirerek anlat.
        4. Gereksiz Kaynak Belirtme İfadelerinin (örn: "Habere göre...", "Raporda belirtildiği üzere...") Sık Tekrarı.
        5. Belirsiz Kısaltmalar (örn: "vs.", "vb.").
        6. URL veya HABER ID'lerini Analiz Metni İçinde Kullanma.
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