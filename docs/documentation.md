Proje Raporu: Akıllı Finans Haberleri Analiz ve Özetleme Platformu (MVP)
Tarih: 18 Mayıs 2025 (Güncellenmiş)
Versiyon: 1.1 (MVP - Detaylı İş Akışlı)
Proje Sahibi: [Senin Adın/Takımın]
1. Giriş ve Amaç
Bu proje, çeşitli güvenilir kaynaklardan (başlangıçta The New York Times ve The Guardian) periyodik olarak finans ve ekonomiyle ilişkili haberleri toplayan, bu haberler arasında yapay zeka (Google Gemini 1.5 Flash modeli kullanılarak) aracılığıyla çapraz tematik ve potansiyel nedensel ilişkiler kuran, anlamlı "gelişen hikaye" grupları oluşturan ve her bir hikaye için kapsamlı bir analiz, özet, kategori ataması ve kaynakça üreten bir platformun Minimum Uygulanabilir Ürün (MVP) sürümünü tanımlamaktadır. Üretilen analizler, kullanıcı arayüzünde (frontend) Server-Sent Events (SSE) aracılığıyla canlıya yakın bir şekilde güncellenir.
Temel Amaçlar:
Kullanıcılara, farklı kaynaklardan gelen karmaşık finansal bilgileri sentezlenmiş ve analiz edilmiş bir şekilde sunmak.
Yüzeysel benzerliklerin ötesine geçerek, farklı olaylar arasında potansiyel olarak var olan örtük bağlantıları ve gelişen temaları ortaya çıkarmak.
Manuel haber takibi ve analizi için harcanan zamanı azaltmak.
Kullanıcıların güncel analizlere kolayca ve otomatik olarak güncellenen bir arayüz üzerinden erişmesini sağlamak.
2. Sistem Mimarisi ve Bileşenleri
Proje, temel olarak iki ana servis, bir veritabanı ve bir istemci tarafı arayüzden oluşan dağıtık bir mimariye sahiptir:
Spring Boot Backend (Java):
Sorumlulukları:
Zamanlanmış görevler (NewsScheduler) aracılığıyla harici haber API'lerinden (NYTimes, Guardian) haber metadata'sını periyodik olarak toplamak.
Toplanan ham haber metadata'sını PostgreSQL veritabanındaki news tablosuna kaydetmek.
Haber toplama işlemi tamamlandıktan sonra Python AI Servisi'nin FastAPI'deki /trigger-analysis endpoint'ini bir HTTP POST isteği ile tetiklemek.
Python AI Servisi'nden gelen işlenmiş analiz sonuçlarını (başarılı analiz edilmiş hikayeler ve gruplanamayan haber ID'leri) almak için bir RESTful API endpoint'i (/api/internal/submit-ai-results) sunmak.
Gelen analiz sonuçlarını ve gruplanamayan haberler için placeholder kayıtlarını PostgreSQL veritabanındaki ilgili tablolara (analyzed_summary_outputs, analyzed_news_links, summary_assigned_categories) Hibernate/JPA aracılığıyla kaydetmek.
Yeni analizler kaydedildiğinde, bağlı olan frontend istemcilerine Server-Sent Events (SSE) üzerinden /api/summary-updates endpoint'i aracılığıyla bildirim göndermek.
Frontend uygulamasının analiz edilmiş hikaye özetlerini ve ilgili verileri çekebilmesi için RESTful API endpoint'leri (/api/summaries, /api/summaries/{id}) sağlamak.
Python AI Servisi (FastAPI):
Sorumlulukları:
Spring Boot tarafından /trigger-analysis endpoint'i aracılığıyla tetiklenmek.
PostgreSQL news tablosundan, analyzed_news_links tablosunda karşılığı olmayan (işlenmemiş) haberleri okumak.
Newspaper3k ve requests kullanarak okunan haberlerin tam metin içeriklerini ve anahtar kelimelerini çekmek.
Google Gemini 1.5 Flash API'sini kullanarak iki aşamalı bir analiz yapmak:
Aşama 1 (Gruplama - group_news_stories_with_gemini): Scrape edilmiş haberler ({id, title, extracted_keywords, content}) arasında potansiyel olarak ilişkili "gelişen hikaye" grupları ({"group_label": ..., "related_news_ids": [...]}) oluşturmak (her grup en az 2 haber).
Aşama 2 (Detaylı Analiz - analyze_individual_story_group): Aşama 1'de oluşturulan her bir grup için, gruptaki haberlerin tam metinlerini kullanarak kapsamlı bir analiz, hikaye başlığı, özet, haberler arası bağlantıların açıklaması, potansiyel etkiler/öngörüler üretmek ve bu hikayeyi önceden tanımlanmış ana kategorilere atamak. Yanıt {story_title, related_news_ids, analysis_summary, main_categories} içerir.
Aşama 2'de üretilen her analysis_summary'nin sonuna standart bir disclaimer metni eklemek.
Nihai işlenmiş veriyi (başarılı analiz edilmiş hikayeler [disclaimer dahil] ve Aşama 1'de gruplanamayan haberlerin ID'leri) yapılandırılmış bir JSON formatında Spring Boot backend'ine /api/internal/submit-ai-results endpoint'ine bir HTTP POST isteği ile geri göndermek.
PostgreSQL Veritabanı:
Tablolar: news, analyzed_summary_outputs, summary_assigned_categories, analyzed_news_links. (Detayları önceki raporlarda ve kodlarda mevcut).
Frontend (HTML, CSS, Vanilla JavaScript - frontend klasöründe):
Sorumlulukları:
Kullanıcıya analiz edilmiş haber özetlerini sunmak.
Sayfa yüklendiğinde Spring Boot /api/summaries endpoint'inden ilk özet listesini çekmek.
Spring Boot /api/summary-updates SSE endpoint'ine bağlanarak yeni analizler geldiğinde bildirim almak ve özet listesini otomatik olarak güncellemek.
Kullanıcının tarihe ve kategoriye göre özetleri filtrelemesine olanak tanımak (filtreleme sunucuya yeni istek göndererek sayfa yenilemesiyle çalışır).
Bir özete tıklandığında, /summary_detail.html?id={summaryId} gibi bir sayfada, /api/summaries/{id} endpoint'inden çekilen verilerle özetin tam metnini ve kaynakça URL'lerini göstermek.
![Sistem Mimarisi Diyagramı - Buraya güncellenmiş akış diyagramı eklenebilir: Spring Boot (veri çeker, DB'ye yazar) -> HTTP Tetikleme -> Python FastAPI -> DB'den Okuma & Scraping -> Gemini Aşama 1 (Gruplama) -> Gemini Aşama 2 (Analiz) -> Python (Disclaimer Ekleme) -> HTTP Sonuç Gönderme -> Spring Boot (Sonuçları alır, DB'ye yazar) -> SSE Bildirimi -> Frontend (Veriyi API'den çeker, SSE ile güncellenir)]
3. Teknoloji Yığını (Bir Öncekiyle Aynı, httpx Eklendi)
Backend (Spring Boot): Java 17+, Spring Boot 3.1.5+, Spring Data JPA, Hibernate, PostgreSQL, Project Reactor, Maven, Lombok, MapStruct.
AI Servisi (Python): Python 3.9+, FastAPI, Uvicorn, Google Gemini 1.5 Flash (API), google-generativeai, httpx, Newspaper3k, NLTK, SQLAlchemy, psycopg2-binary, python-dotenv, Pydantic.
Veritabanı: PostgreSQL.
Frontend: HTML5, CSS3, Vanilla JavaScript.
4. Detaylı İş Akışı (Güncellenmiş)
4.1. Günlük Haber Toplama ve AI Tetikleme (Spring Boot)
(Bir önceki rapordaki gibi, sonunda Python FastAPI'nin /trigger-analysis endpoint'ini HTTP POST ile tetikler)
4.2. AI Analiz Süreci (Python AI Servisi)
(Bir önceki rapordaki gibi, Aşama 1 ve Aşama 2 Gemini çağrılarını içerir. Ana farklar:)
İşlenmemiş Haber Seçimi: news tablosundan, id'si analyzed_news_links'te original_news_id olarak bulunmayanlar seçilir.
Scraping: Tam metin ve Newspaper3k ile extracted_keywords çekilir.
Gemini Aşama 1 (Gruplama): Girdi {id, title, extracted_keywords, content}. Çıktı [{"group_label": ..., "related_news_ids": [...]}, ...]. Her grup en az 2 haber içerir.
Gemini Aşama 2 (Detaylı Analiz): Her grup için girdi, o gruba ait haberlerin {id, title, extracted_keywords, content} bilgileri ve group_label'dır. Çıktı {story_title, related_news_ids, analysis_summary, main_categories}. analysis_summary içinde URL olmaz.
Sonuçların Zenginleştirilmesi (main.py): Her başarılı Aşama 2 sonucuna (analyzed_story_result):
analysis_summary'nin sonuna standart DEFAULT_DISCLAIMER eklenir.
(Kaldırıldı): references alanı artık burada eklenmiyor.
Payload Hazırlama: Spring Boot'a gönderilecek JSON:
{
    "analyzed_stories": [ 
        // Her biri: {story_title, related_news_ids, analysis_summary (disclaimer dahil), main_categories}
    ],
    "ungrouped_ids": [ /* Aşama 1'e giren ama hiçbir gruba atanamayan haber ID'leri */ ] 
}
Sonuçların Spring Boot'a Gönderilmesi (result_sender.py): Yukarıdaki payload, httpx ile Spring Boot'un /api/internal/submit-ai-results endpoint'ine POST edilir.
4.3. AI Sonuçlarının Kaydedilmesi ve SSE Bildirimi (Spring Boot)
Gelen Verinin Alınması (InternalApiController): JSON payload'ı AiProcessingResultDTO'ya map edilir.
Veritabanı İşlemleri (ProcessedAiResultsService - @Transactional):
analyzed_stories için AnalyzedSummaryOutput ve AnalyzedNewsLink kayıtları oluşturulur ve kaydedilir.
ungrouped_ids için "UNGROUPED_PLACEHOLDER" AnalyzedSummaryOutput kaydına AnalyzedNewsLink kayıtları oluşturulur.
SSE Bildirimi (ProcessedAiResultsService -> NotificationService): Veritabanı kaydı başarıyla tamamlandıktan sonra, NotificationService.sendNewSummariesNotification() çağrılarak /api/summary-updates SSE endpoint'ine bağlı olan tüm frontend istemcilerine "yeni_veriler_hazir" olayı gönderilir.
4.4. Frontend Veri Gösterimi ve Otomatik Güncelleme
İlk Yükleme (frontend/script.js): index.html yüklendiğinde, /api/summaries endpoint'inden (varsayılan filtrelerle) özetler çekilir ve listelenir.
SSE Bağlantısı (frontend/script.js): Sayfa yüklendiğinde /api/summary-updates SSE endpoint'ine bağlanılır.
Otomatik Güncelleme: Sunucudan new_summaries_available olayı geldiğinde, fetchSummaries() fonksiyonu tekrar çağrılarak ana sayfadaki özet listesi en son verilerle güncellenir.
Filtreleme (frontend/script.js ve Spring Boot Controller): Ana sayfadaki tarih veya kategori filtreleri kullanıldığında, frontend yeni URL'e (örn. /summaries?category=EKONOMİ) yönlenir. Spring Boot Controller'ı bu isteği alır, filtrelenmiş veriyi DB'den çeker ve yeni bir HTML sayfasını (Thymeleaf ile) render ederek kullanıcıya gönderir.
Detay Sayfası (frontend/summary_detail.js): Bir özete tıklandığında, summary_detail.html?id={id} sayfası açılır. JavaScript, /api/summaries/{id} endpoint'inden özet detaylarını (başlık, analiz [disclaimer dahil], kategoriler) ve Spring Boot'un AnalyzedNewsLink üzerinden topladığı kaynakça URL'lerini çeker ve sayfayı doldurur.
5. Kullanılan Ana Kategoriler (Gemini Aşama 2 İçin)
EKONOMİ, PİYASALAR, SİYASET, JEOPOLİTİK, TEKNOLOJİ, ENERJİ, İKLİM
6. Sorumluluk Reddi Metni (disclaimer)
"Bu içerik yapay zeka ile otomatik olarak üretilmiş olup, sağlanan haberlere dayanmaktadır ve genel bilgilendirme amaçlıdır. Yatırım tavsiyesi niteliği taşımaz." (Python AI servisi tarafından her analysis_summary'nin sonuna eklenir).