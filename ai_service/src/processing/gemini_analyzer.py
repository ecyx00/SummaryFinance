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
        # GÖREV TANIMI: STRATEJİK FİNANSAL ANALİZ İLE GELİŞEN HİKAYE GRUPLARI OLUŞTURMA

        Sen, küresel ekonomi, finansal piyasalar, şirket stratejileri, teknolojik kırılımlar ve jeopolitik dinamikler arasında karmaşık, genellikle gözden kaçan bağlantıları tespit etme; olaylar arasındaki zincirleme reaksiyonları ve altta yatan makro temaları sentezleme konusunda uzmanlaşmış, üst düzey bir stratejik analiz ve araştırma direktörüsün. Temel görevin, sinyali gürültüden ayırmak ve farklı bilgi parçacıklarından bütüncül bir anlayış inşa etmektir.

        SANA VERİLEN GÖREV: Aşağıda JSON formatında sunulan bir dizi haber makalesini (her biri `id`, `title`, `extracted_keywords` ve `content` alanlarını içerir) derinlemesine inceleyeceksin. Bu inceleme sonucunda, ilk bakışta bağımsız veya alakasız gibi görünen olaylar arasında anlamlı, disiplinlerarası, çapraz tematik ve/veya potansiyel nedensel ilişkiler kuran, birbirinden belirgin şekilde ayrışan **"gelişen hikaye" grupları** oluşturman beklenmektedir.

        ## TEMEL PRENSİPLER VE KESİNLİKLE KAÇINILMASI GEREKENLER:
        1.  **FARKLI OLAYLAR ARASI KÖPRÜLER KUR (KRİTİK!):** Odak noktan, **ASLA ve ASLA** sadece aynı olayı (örneğin, aynı şirket duyurusunu veya aynı ekonomik veriyi) farklı kaynaklardan bildiren, birbirinin tekrarı veya çok benzer içeriklere sahip haberleri bir araya getirmek DEĞİLDİR. Bu tür gruplamalar **KESİNLİKLE İSTENMEMEKTEDİR**. Bunun yerine, bir olayın, normalde ilgisiz görünen başka bir alandaki bir olayı nasıl etkilediğini, tetiklediğini, onunla nasıl birleşerek daha büyük ve yeni bir anlam katmanı oluşturduğunu veya daha geniş bir makro trendin parçası olduğunu gösteren **özgün ve içgörülü** gruplar oluşturmalısın. Örnek: Bir ülkedeki kuraklık haberinin (iklim), belirli tarım emtialarının fiyatlarını (piyasalar) nasıl etkilediği ve bunun da gıda enflasyonu (ekonomi) ve tüketici şirketlerinin kâr marjları (şirket haberleri) üzerinde nasıl bir baskı oluşturduğu gibi çoklu bağlantılar ara.
        2.  **DERİN VE ANLAMLI BAĞLANTILAR:** Yalnızca birkaç ortak anahtar kelimenin varlığına dayalı yüzeysel veya zorlama gruplamalar yapmaktan **KESİNLİKLE KAÇIN**. Grupladığın haberlerin içerikleri arasında somut, mantıksal bir akış, kanıtlanabilir veya güçlü bir şekilde çıkarımlanabilir bir etki mekanizması veya birbirini tamamlayan/açıklayan güçlü bir ortak tema olmalıdır. "Bu haberler 'ekonomi' hakkında" gibi genel etiketler yeterli değildir; spesifik ve dinamik bir ilişki tanımlanmalıdır.
        3.  **MİNİMUM GRUP BÜYÜKLÜĞÜ:** Oluşturacağın **her bir "gelişen hikaye" grubu MUTLAKA en az 2, tercihen 3 veya daha fazla haber içermelidir.** Tek haberden oluşan gruplar kesinlikle kabul edilmeyecektir ve bir değeri yoktur.
        4.  **GRUP SAYISI VE KALİTESİ:** Belirli bir sayıda grup oluşturma zorunluluğun YOKTUR. Öncelik, gerçekten anlamlı, birbirinden net bir şekilde ayrışan ve güçlü iç bağlantılara sahip "gelişen hikayeler" tespit etmektir. Eğer o günkü haber seti içerisinde bu nitelikte bariz ve güçlü çapraz ilişkisel temalar bulunmuyorsa, az sayıda (hatta hiç) grup üretmen, zayıf veya anlamsız gruplar üretmenden çok daha iyidir. **Kalite, nicelikten kesinlikle daha önemlidir.** Anlamsız veya zorlama gruplar oluşturmaktan kaçın.
        5.  **GRUPLAMA ODAĞI:** Haberlerin konuları farklı olabilir (örn: biri teknoloji, diğeri politika), ancak aralarında bir "hikaye" oluşturacak bir etkileşim, sonuç veya ortak bir üst tema olmalıdır.

        ## BEKLENEN DÜŞÜNME VE ANALİZ ŞEKLİ (ÖRNEK AKIL YÜRÜTME İLE NE İSTEDİĞİMİ ANLA):
        *   **İSTENEN ÖRNEK 1:** "Bir büyük yarı iletken üreticisinin yeni nesil çip üretiminde yaşadığı bir darboğaz haberi (ID: tech01), bu çipleri kullanan bir otomobil üreticisinin üretim hedeflerini düşürdüğünü açıkladığı bir haberle (ID: auto05) ve bu durumun küresel tedarik zincirlerindeki kırılganlığa işaret eden bir analistle yapılan röportajla (ID: econ03) birleşebilir. Bu grubun etiketi 'Yarı İletken Krizi ve Otomotiv Sektörüne Etkileri' gibi bir şey olabilir." Bu, farklı sektörlerdeki olayların birbirini nasıl etkilediğini gösteren iyi bir "gelişen hikaye" örneğidir.
        *   **İSTENEN ÖRNEK 2:** "Gelişmekte olan bir ülkede yaşanan beklenmedik bir siyasi istikrarsızlık haberi (ID: geo07), o ülkenin para biriminde ani değer kaybı yaşandığına dair bir piyasa haberiyle (ID: market02) ve o ülkede büyük yatırımları olan uluslararası bir şirketin risk değerlendirmesini güncellediği bir haberle (ID: biz04) anlamlı bir grup oluşturabilir. Etiket: 'X Ülkesindeki Siyasi Belirsizliğin Finansal Piyasalara ve Uluslararası Yatırımlara Yansıması'."
        *   **İSTENMEYEN ÖRNEK:** "Apple Yeni iPhone Modelini Tanıttı" (ID: apple01), "Samsung Yeni Galaxy Modelini Duyurdu" (ID: samsung01), "Xiaomi'den Yeni Amiral Gemisi Telefon" (ID: xiaomi01) haberlerini "Yeni Akıllı Telefon Modelleri" gibi bir etiketle gruplamak, bu görevin amacı dışındadır. Bu haberler benzer konularda olsa da, aralarında özel bir etkileşim veya gelişen bir hikaye olmayabilir. Ancak, bu haberlere ek olarak "Telekom Şirketleri 5G Altyapı Yatırımlarını Hızlandırıyor" (ID: telco01) gibi bir haber varsa ve yeni telefonların bu 5G altyapısını kullanacağı vurgulanıyorsa, o zaman "Yeni Nesil Akıllı Telefonlar ve 5G Altyapı Gelişmeleri" gibi bir grup daha anlamlı olabilir.

        ## ANALİZ EDİLECEK HABERLER (JSON Formatında):
        ```json
        {news_json}
        ```

        SENDEN İSTENEN ÇIKTI:
        Lütfen analizinin sonucunu, **KESİNLİKLE** aşağıdaki JSON formatında bir **liste** olarak ver. Bu listenin her bir elemanı, yukarıdaki prensipler doğrultusunda belirlediğin bir "gelişen hikaye" grubunu temsil eden bir JSON objesi olmalıdır.
        Her bir grup objesi şu iki anahtarı içermelidir:
        1.  `group_label`: String. Bu gruptaki haberlerin oluşturduğu, yukarıda tanımlanan "gelişen hikaye"yi veya çapraz tematik bağlantıyı yansıtan, kısa (tercihen 3-10 kelime), öz ve analitik bir etiket. Bu etiket, haberlerin basit bir birleşimi olmamalı, aralarındaki **dinamiği** veya **ortak sonucu** ifade etmelidir.
        2.  `related_news_ids`: List[String]. Bu "gelişen hikaye" grubunu oluşturan ve sana verilen haberlerin orijinal `id`'lerini içeren bir liste. Bu listeye sadece gerçekten bu hikayeyle güçlü ve anlamlı bir bağlantısı olan haberlerin ID'lerini ekle.

        Çıktının tamamı bir JSON listesi olmalıdır. Yanıtının başında veya sonunda **kesinlikle** başka hiçbir metin, açıklama, selamlama, giriş/sonuç cümlesi veya markdown formatlaşması (```json gibi) OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki listeyi döndür.

        ÖRNEK ÇIKTI FORMATI:
        ```json
        {example_output_json}
        ```

        Eğer verilen haberler arasında yukarıdaki katı prensiplere uygun, en az iki (tercihen üç veya daha fazla) haber içeren ve farklı olaylar arasında anlamlı, derin ve içgörülü bağlantılar kuran hiçbir "gelişen hikaye" grubu oluşturamıyorsa, **boş bir JSON listesi `[]` döndür.**
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
        1. Giriş ve Merkezi Tema: Bu haber grubunun merkezindeki ana olay(lar)ı ve bunların oluşturduğu, senin belirlediğin merkezi temayı veya ana hikayeyi net bir şekilde tanımlayarak başla.
        2. Haberler Arası Bağlantıların Derinlemesine Açıklanması: Gruptaki haberlerde anlatılan ana olayları, önemli verileri veya kilit argümanları belirgin bir şekilde ifade ederek (örn: "[Şirket adı]'nın açıkladığı rekor kar...", "X ülkesinin enerji politikalarındaki ani değişiklik...", "[Merkez Bankası Başkanı]'nın enflasyonla ilgili endişelerini dile getirmesi..." gibi), bu farklı olaylar veya bilgiler arasında nasıl bir ilişki, etkileşim, ardışıklık veya potansiyel nedensellik görüyorsun? Bir olay diğerini nasıl tetiklemiş, etkilemiş veya hangi ortak zemin üzerinde birleşmiş olabilir? Lütfen çıkarımlarını, verilen haber metinlerinden ve (varsa) extracted_keywords alanlarından spesifik pasajlara veya bilgilere atıfta bulunarak kanıtla ve detaylandır. Yüzeysel benzerliklerin ötesine geçerek altta yatan dinamikleri ve bağlantı noktalarını ortaya koy. Olayları sıralamak yerine, aralarındaki mantıksal akışı ve birbirlerini nasıl etkilediklerini vurgulayan bir anlatı oluştur.
        3. Potansiyel Etkiler ve Öngörüler: Geliştirdiğin merkezi tema ve ortaya koyduğun bağlantılar ışığında, bu gelişmelerin daha geniş anlamda (ekonomik, politik, sektörel, teknolojik vb.) olası kısa ve orta vadeli etkileri neler olabilir? Bu analizine dayanarak hangi potansiyel sonuçlar veya gelecekteki gelişmeler öngörülebilir?
        4. URL KULLANMA: Bu analiz metni içinde kesinlikle hiçbir URL linki kullanma.
        main_categories:
        Aşağıdaki önceden tanımlanmış ana kategori listesinden, bu analiz ettiğin genel hikayeye, bağlantılara ve potansiyel etkilere en uygun olan 1 veya 2 kategoriyi seçerek bir JSON listesi olarak ver:
        {categories_str}
        
        ÇIKTI FORMATI (JSON OBJESİ):
        Yanıtını KESİNLİKLE aşağıdaki JSON formatında tek bir obje olarak ver. Yanıtının başında veya sonunda kesinlikle başka hiçbir metin, açıklama veya giriş/sonuç cümlesi OLMAMALIDIR. Sadece ve sadece istenen JSON formatındaki objeyi döndür.

        ```json
        {example_output_json}
        ```

        ÜSLUP VE AKICILIK:
        - Lütfen analiz metnini, bir insan analist tarafından yazılmış gibi doğal, akıcı ve çeşitli bir dil kullanarak oluştur.
        - Aynı kelime veya cümle yapılarını sık sık tekrarlamaktan kaçın.
        - Olayları ve çıkarımları birbirine bağlarken zengin bir bağlaç ve ifade çeşitliliği kullan.
        - Okuyucunun kolayca takip edebileceği, mantıksal bir argüman akışı oluştur.

        KAÇINILMASI GEREKEN İFADELER:
        Lütfen analiz metninde aşağıdaki veya benzeri ifadeleri KULLANMAKTAN KAÇIN:
        - "Bu haberde...", "İlk haber...", "İkinci haber..." gibi doğrudan haberlere numara veya sıra ile referans verme. Bunun yerine, haberin içeriğine veya konusuna atıfta bulun (örn: "Kredi notu düşüşünü ele alan gelişme...", "Avrupa Komisyonu'nun büyüme tahminleriyle ilgili rapor...").
        - "Bu durum..." ifadesini aşırı kullanma. Bunun yerine, cümlenin öznesini veya olayı tekrar belirterek veya daha çeşitli bağlaçlar kullanarak akıcılığı artır. (Örn: "Kredi notundaki düşüş, yatırımcı güvenini sarstı." gibi ifadeler tercih et.)
        - "Habere göre...", "Raporda belirtildiği üzere..." gibi doğrudan kaynak belirtme ifadelerini sık sık tekrarlama. Bilginin haberlerden geldiği zaten varsayılmaktadır.

        ÖNEMLİ NOTLAR:
        - Analizini sadece ve sadece sana verilen haber metinlerine, başlıklarına ve anahtar kelimelerine dayandır. Dışarıdan ek bilgi veya varsayım kullanma.
        - Objektif, dengeli ve analitik bir dil kullanmaya özen göster.
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