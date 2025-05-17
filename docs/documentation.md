# Proje Raporu: Finans Haberleri Özetleyici ve Analiz Platformu

**Tarih:** 11 Mayıs 2025
**Versiyon:** 1.0

## 1. Proje Amacı ve Kapsamı

### 1.1. Proje Amacı
Bu projenin temel amacı, finans, ekonomi, siyaset, teknoloji ve parayı doğrudan veya dolaylı olarak etkileyen diğer önemli kategorilerdeki güncel haberleri çeşitli güvenilir kaynaklardan otomatik olarak toplamak, bu haberleri yapay zeka (AI) kullanarak analiz etmek, aralarındaki ilişkileri tespit etmek ve kullanıcılara anlamlı, özetlenmiş ve analitik bir bakış açısı sunmaktır. Platform, kullanıcıların farklı kaynaklardan gelen karmaşık bilgileri hızlı ve verimli bir şekilde tüketmelerini, önemli trendleri ve olayları kolayca fark etmelerini sağlamayı hedefler.

### 1.2. Proje Kapsamı
*   **Veri Toplama:** Belirlenen haber API'lerinden (başlangıçta The New York Times ve The Guardian) periyodik olarak haber metadata'sı çekilecektir.
*   **İçerik Çekme:** Haber metadata'sındaki URL'ler kullanılarak haberlerin tam metin içerikleri web scraping yöntemleriyle elde edilecektir.
*   **AI Analizi ve Özetleme:**
    *   Toplanan ve içerikleri çekilen haberler arasındaki ilişkiler AI ile tespit edilecektir.
    *   Dinamik olarak belirlenen ilişkili haber grupları için ayrı ayrı analizler ve özetler üretilecektir.
    *   Üretilen her özet/analiz, önceden tanımlanmış genel uygulama kategorilerine (Finans, Siyaset, Teknoloji vb.) atanacaktır.
*   **Depolama:** Haber metadata'sı, AI tarafından üretilen özetler ve ilişkili bilgiler PostgreSQL veritabanında saklanacaktır.
*   **Sunum:** Kullanıcıların bu analiz edilmiş ve özetlenmiş haber "hikayelerine" bir web arayüzü üzerinden erişmeleri sağlanacaktır.
*   **Hedeflenen Çıktı Frekansı:** Başlangıçta günlük olarak yeni haberler çekilecek ve günlük olarak yeni "hikaye özetleri" üretilecektir. Haftalık kapsamlı analizler de düşünülebilir.

### 1.3. Çözülmeye Çalışılan Problem
Günümüz bilgi çağında, özellikle finans gibi dinamik ve birçok faktörden etkilenen bir alanda, kullanıcılar çok sayıda farklı kaynaktan gelen haberleri takip etmek, bunlar arasında bağlantı kurmak ve anlamlı sonuçlar çıkarmak için ciddi zaman harcamaktadır. Bu proje, bu süreci otomatize ederek ve AI destekli analizler sunarak kullanıcılara zaman kazandırmayı ve daha derinlemesine bir anlayış sunmayı amaçlamaktadır.

## 2. Sistem Mimarisi ve İş Akışı

### 2.1. Genel Mimari
Proje, temel olarak üç ana bileşenden oluşacaktır:
1.  **Spring Boot Backend (Veri Toplayıcı ve API Sağlayıcı):** Haber API'lerinden metadata çeker, veritabanına kaydeder ve frontend'e veri sunan API'leri barındırır.
2.  **Python AI Servisi (Analiz ve Özetleme Motoru):** Veritabanından haberleri okur, içeriklerini çeker, AI (Google Gemini) ile analiz eder, ilişkili haber grupları oluşturur, özetler üretir ve bu özetleri kategorize ederek veritabanına kaydeder.
3.  **Frontend (Kullanıcı Arayüzü):** Kullanıcıların analiz edilmiş özetlere erişmesini sağlar. (Bu raporun ana odağı backend ve AI servisidir.)

### 2.2. İş Akışı
1.  **Günlük Veri Çekme (Spring Boot Scheduler):**
    *   Belirlenen saatte (örn. her gün sabah 5) otomatik olarak tetiklenir.
    *   Son 24 saatin haberlerini hedefler.
    *   `application.properties` dosyasında tanımlı kategoriler ve bu kategorilere karşılık gelen API filtreleri kullanılarak her API kaynağından (NYTimes, Guardian) haber metadata'sı çekilir.
    *   Her kategori için API'nin izin verdiği maksimum sayıda sayfa dinamik sayfalama ile çekilir (API rate limitlerine uygun gecikmelerle).
    *   Çekilen haberlerin metadata'sı (`url`, `title`, `publicationDate`, **kaynaktaki ham `section` adı**, `source`) ve haberin çekildiği zaman (`fetchedAt`) veritabanındaki `news` tablosuna kaydedilir. URL bazlı tekilleştirme yapılır.
2.  **Günlük Analiz ve Özetleme (Python AI Servisi Scheduler):**
    *   Spring Boot'un veri çekme işlemi tamamlandıktan sonra (veya bağımsız bir zamanlamayla, örn. her gün sabah 7) tetiklenir.
    *   Veritabanındaki `news` tablosundan son 24 saatte eklenen (veya henüz işlenmemiş) haberleri okur.
    *   Her haberin tam metnini (`content`) `url`'ini kullanarak web scraping yöntemleriyle çeker.
    *   Tüm çekilen haber içeriklerini ve metadata'larını kullanarak:
        *   AI (Gemini) ile haberler arasındaki anlamsal ilişkileri, bağlantıları ve ortak temaları belirler.
        *   Bu ilişkilere göre haberleri dinamik olarak gruplandırır (bir "hikaye" veya "news cluster" oluşturur). Bir haber birden fazla gruba dahil olabilir.
        *   Her bir grup için AI (Gemini) kullanarak ayrı bir analiz ve özet metni (`summary_text`) oluşturur. Bu metin, gruptaki haberlerin sentezini ve potansiyel çıkarımlarını içerebilir.
        *   Her bir oluşturulan "hikaye özeti" için AI veya kural tabanlı bir sistemle bir veya daha fazla genel uygulama kategorisi (`assigned_categories` - örn: "FINANCE", "POLITICS") belirler.
        *   Oluşturulan her hikaye özetini (`story_title`, `summary_text`, `publication_date` (grubun ana tarihi), `generated_at`, `assigned_categories`) `analyzed_summary_outputs` tablosuna kaydeder.
        *   Bu özetin hangi orijinal haberlere dayandığını `analyzed_news_links` ara tablosuna (`summary_output_id`, `news_id`) kaydeder.
3.  **Özetlerin Sunumu (Frontend -> Spring Boot API):**
    *   Kullanıcı, web arayüzünden haber özetlerini görüntülemek istediğinde (örn. belirli bir tarih, kategori veya anahtar kelime ile filtreleyerek).
    *   Frontend, Spring Boot API'sine istek gönderir.
    *   Spring Boot API'si (`SummaryController`), `analyzed_summary_outputs` tablosunu ve ilişkili tabloları sorgulayarak ilgili özetleri ve kaynak haber linklerini (gerekirse) çeker.
    *   Çekilen veriyi frontend'e JSON formatında gönderir.
    *   Frontend, bu veriyi kullanıcıya anlamlı bir şekilde sunar.

## 3. Spring Boot Backend Tasarımı

### 3.1. Ana Teknolojiler
*   Java (JDK 17+)
*   Spring Boot 3.x
*   Spring WebFlux (Asenkron API istemcileri için `WebClient`)
*   Project Reactor (`Flux`, `Mono` reaktif akışlar için)
*   Spring Data JPA / Hibernate (Veritabanı etkileşimi için)
*   Lombok (Boilerplate kodu azaltmak için)
*   MapStruct (DTO ve Entity dönüşümleri için)

### 3.2. Katmanlı Mimari
*   **Controller Katmanı (`NewsController`, `SummaryController`):** Gelen HTTP isteklerini karşılar, gerekli doğrulamaları yapar ve Service katmanını çağırır. Sonuçları `ResponseEntity` olarak döndürür.
*   **Service Katmanı (`NewsService`, `SummaryService`):** İş mantığını içerir.
    *   `NewsService`: Haber API client'larını yönetir, veri çekme, tekilleştirme ve `news` tablosuna kaydetme işlemlerini koordine eder. Reaktif akışları yönetir.
    *   `SummaryService`: `analyzed_summary_outputs` ve ilişkili tablolardan özetleri okuyup DTO'lara dönüştürür.
*   **Repository Katmanı (`NewsRepository`, `AnalyzedSummaryOutputRepository` vb.):** Spring Data JPA arayüzleri kullanılarak veritabanı CRUD işlemleri ve özel sorgular tanımlanır.
*   **Client Katmanı (`NewsSourceClient` arayüzü, `NYTimesClient`, `GuardianClient`):** Harici haber API'lerine istek atmak, yanıtları almak ve ham veriyi parse edip `NewsDTO`'ya dönüştürmekten sorumludur. Dinamik sayfalama ve API rate limitlerine uygun gecikme mantığını içerir.
*   **Entity Katmanı (`News`, `AnalyzedSummaryOutput`, `AnalyzedNewsLink`):** Veritabanı tablolarını temsil eden JPA entity sınıfları.
*   **DTO Katmanı (`NewsDTO`, `SummaryDTO` vb.):** Katmanlar arası veri transferi ve API yanıtları için kullanılan veri transfer nesneleri.
*   **Mapper Katmanı (`NewsMapper` vb.):** MapStruct kullanılarak Entity ve DTO'lar arası dönüşümleri sağlar.
*   **Scheduler Katmanı (`NewsScheduler`):** `@Scheduled` anotasyonu ile periyodik haber çekme işlemini tetikler.
*   **Config Katmanı (`application.properties`):** Veritabanı bağlantıları, API anahtarları, cron ifadeleri, kategori filtreleri, gecikme süreleri gibi yapılandırılabilir tüm parametreleri içerir.

### 3.3. Haber Çekme Mekanizması Detayları
*   **Zamanlama:** `NewsScheduler`, `NewsService`'in `fetchAndSaveAllConfiguredNewsReactive()` metodunu cron ifadesine göre tetikler.
*   **Kategori ve Filtre Yönetimi:**
    *   `application.properties` dosyasında her API kaynağı için çekilecek kategori anahtarları (`app.nytimes.enabled.keys`, `app.guardian.enabled.keys`) ve bu anahtarlara karşılık gelen API'ye özgü filtre string'leri (`nytimes.filter.KEY_ISMI`, `guardian.filter.KEY_ISMI`) tanımlanır.
    *   `NewsService`, `Environment` servisini kullanarak bu anahtarları ve filtreleri okur.
*   **Client Yönetimi:**
    *   `NewsService`, `List<NewsSourceClient>` üzerinden tüm tanımlı client'ları (NYTimes, Guardian) iterate eder.
    *   Her client için, o client'a ait aktif kategori anahtarlarını alır.
    *   **Sıralı Kategori İşleme:** Her client için, o client'a ait tüm kategoriler `Flux.fromIterable().concatMap(..., 1)` kullanılarak **sıralı** bir şekilde işlenir. Bu, tek bir API kaynağına aynı anda çok fazla yüklenmeyi önler.
    *   `concatMap` içindeki her bir `topicKey` için, `environment.getProperty()` ile API'ye özgü filtre string'i alınır ve `client.fetchNewsByTopic()` metoduna `startDate`, `endDate` ile birlikte geçirilir.
*   **Kaynaklar Arası İşleme:**
    *   Guardian client'ının tüm kategorileri işlendikten sonra, NYTimes client'ının kategorileri işlenmeye başlar (`Flux.concat(guardianStream, Mono.delay().thenMany(nytStream))`). Aralarına `interSourceDelayMs` kadar bir gecikme konulur. Bu, en hassas olan NYTimes API'sine geçmeden önce bir bekleme sağlar.
*   **Client İçi Dinamik Sayfalama ve Gecikme:**
    *   Her `NewsSourceClient` implementasyonu (`NYTimesClient`, `GuardianClient`), `fetchNewsByTopic` metodunda, aldığı filtre ve tarih aralığı için API'nin izin verdiği tüm sayfaları çekmek üzere dinamik sayfalama yapar (`Flux.range().concatMap(page -> fetchPageData(...)).takeWhile(...)`).
    *   API rate limitlerine uymak için her sayfa isteği arasında (`delayElements` ile) yapılandırılabilir bir gecikme (`api.client.delay.XXX.ms`) uygulanır.
    *   Sayfalama, API'den boş yanıt geldiğinde veya API'nin belirttiği toplam sayfa sayısına ulaşıldığında (Guardian) veya maksimum deneme sayısına (NYTimes `MAX_PAGES_NYT`) ulaşıldığında durdurulur.
*   **Veri Akışı ve Birleştirme:**
    *   Client'lardan dönen `Flux<NewsDTO>`'lar, `NewsService` içinde `Flux.concat()` (veya gerekirse `Flux.merge()`) ile tek bir ana akışta birleştirilir.
    *   Bu birleştirilmiş akıştan `.collectList()` ile tüm `NewsDTO`'lar toplanır.
    *   Toplanan liste `deduplicateAndSaveNews()` metoduna gönderilir.
*   **Veritabanı Kaydı:**
    *   `deduplicateAndSaveNews()` metodu, gelen DTO listesindeki URL'leri, veritabanındaki mevcut URL'lerle tek bir sorguda karşılaştırır.
    *   Sadece yeni olan haberler `NewsMapper` ile `News` entity'sine dönüştürülür, `fetchedAt` zamanı atanır ve `NewsRepository.saveAll()` ile kaydedilir. Bu işlem `Schedulers.boundedElastic()` üzerinde yapılır.

## 4. Veritabanı Tasarımı (PostgreSQL)

### 4.1. `news` Tablosu
*   **Amacı:** Haber API'lerinden çekilen ham haber metadata'sını saklamak. Spring Boot tarafından yazılır, Python tarafından okunur.
*   **Sütunlar:**
    *   `id`: `BIGSERIAL` (Otomatik artan `BIGINT`), Primary Key
    *   `title`: `TEXT`, Not Null (Haber başlığı)
    *   `url`: `TEXT`, Not Null, Unique (Haberin orijinal URL'i, tekilleştirme için anahtar)
    *   `publication_date`: `TIMESTAMP WITH TIME ZONE`, Not Null (Haberin yayınlanma tarihi ve saati)
    *   `section`: `VARCHAR(255)`, Not Null (Haberin API kaynağından geldiği **ham** bölüm/kategori adı, örn: "Business Day", "World news", "Technology")
    *   `source`: `VARCHAR(255)`, Not Null (Haber kaynağının adı, örn: "The New York Times", "The Guardian")
    *   `fetched_at`: `TIMESTAMP WITH TIME ZONE`, Not Null (Bu kaydın veritabanına eklendiği zaman)
*   **İndeksler:** `url` (unique), `publication_date`, `section`, `source`.

### 4.2. `analyzed_summary_outputs` Tablosu
*   **Amacı:** Python AI servisinin, dinamik olarak grupladığı ilişkili haberler için ürettiği analiz/özet metinlerini ve bu özetin atandığı genel uygulama kategorilerini saklamak. Python tarafından yazılır, Spring Boot tarafından okunur.
*   **Sütunlar:**
    *   `id`: `BIGSERIAL`, Primary Key
    *   `story_title`: `TEXT` (AI'ın bu ilişkili haber grubuna/temaya verdiği opsiyonel başlık)
    *   `summary_text`: `TEXT`, Not Null (AI tarafından üretilen uzun analiz/özet metni. PostgreSQL'in `TEXT` tipi çok büyük metinleri kaldırabilir.)
    *   `publication_date`: `DATE` (Bu "hikayenin" veya ilişkili haberlerin ağırlıklı olduğu tarih, günlük gruplama için kullanılabilir)
    *   `generated_at`: `TIMESTAMP WITH TIME ZONE`, Not Null (Bu özetin oluşturulma zamanı)
    *   `assigned_categories`: `TEXT[]` (PostgreSQL string dizisi tipi. AI'ın bu özeti atadığı **bizim standart genel uygulama kategorilerimizin** listesi, örn: `{"FINANCE", "TECHNOLOGY"}`).
*   **İndeksler:** `publication_date`, `assigned_categories` (GIN indeksi ile dizin içi arama için).

### 4.3. `analyzed_news_links` Tablosu (Ara Tablo)
*   **Amacı:** Her bir `analyzed_summary_outputs` kaydının (yani her bir "hikaye özeti"), hangi orijinal haberlere (`news` tablosundaki) dayandığını gösteren Many-to-Many ilişkiyi kurmak. Python tarafından yazılır, Spring Boot tarafından okunabilir.
*   **Sütunlar:**
    *   `id`: `BIGSERIAL`, Primary Key
    *   `summary_output_id`: `BIGINT`, Not Null, Foreign Key -> `analyzed_summary_outputs(id)`
    *   `news_id`: `BIGINT`, Not Null, Foreign Key -> `news(id)`
*   **İndeksler:** `summary_output_id`, `news_id`.
*   **Constraint:** `UNIQUE(summary_output_id, news_id)`.

### 4.4. Şema Yönetimi
*   Tercihen, Spring Boot uygulamasının `spring.jpa.hibernate.ddl-auto=update` ayarı ile geliştirme ortamında şemayı otomatik olarak yönetmesi. Production için `validate` veya manuel DDL scriptleri (Flyway/Liquibase ile) düşünülebilir. (Bu konu mentor ile tartışılacak).

## 5. Python AI Servisi Tasarımı (Genel Hatlar)

### 5.1. Ana Sorumluluklar
1.  **Veri Okuma:** PostgreSQL `news` tablosundan periyodik olarak (örn. günlük) yeni eklenen haber metadata'sını okumak.
2.  **İçerik Çekme (Web Scraping):** Okunan haberlerin `url`'lerini kullanarak web sayfalarından tam metin içeriklerini çekmek (örn. `requests`, `BeautifulSoup`, `Scrapy` veya `Playwright` kütüphaneleri ile). Her sitenin yapısı farklı olacağı için esnek bir scraping altyapısı gerekebilir.
3.  **AI Destekli Analiz (Google Gemini API):**
    *   Çekilen haber içeriklerini ve metadata'larını Gemini API'sine göndererek:
        *   Haberler arasındaki anlamsal ilişkileri, bağlantıları, ortak temaları ve potansiyel etkileşimleri tespit etmek.
        *   Bu ilişkilere göre haberleri dinamik olarak gruplandırmak.
4.  **Özet ve Kategorizasyon Üretme:**
    *   Her bir dinamik haber grubu için Gemini API'sini kullanarak:
        *   Kapsamlı bir analiz ve özet metni (`summary_text`) oluşturmak. Bu metin, gruptaki haberlerin sentezini, önemli noktalarını ve potansiyel çıkarımlarını/beklentilerini içerebilir.
        *   Oluşturulan bu "hikaye özeti" için bir veya daha fazla genel uygulama kategorisi (`assigned_categories` - örn: "FINANCE", "POLITICS", "TECHNOLOGY") belirlemek. AI bu atamayı yapabilir veya önceden tanımlanmış kurallar ve anahtar kelimelerle desteklenebilir.
        *   Opsiyonel olarak bu "hikayeye" bir başlık (`story_title`) atamak.
5.  **Sonuçları Veritabanına Kaydetme:**
    *   Üretilen her "hikaye özetini" `analyzed_summary_outputs` tablosuna kaydetmek.
    *   Bu özetin hangi orijinal haberlere dayandığını `analyzed_news_links` tablosuna kaydetmek.
6.  **Zamanlama:** Bu işlemlerin de periyodik olarak (örn. günlük, haber çekme işlemi bittikten sonra) çalışması için bir zamanlama mekanizması (APScheduler, Celery veya basit bir cron job) gerekecektir.

### 5.2. Kullanılacak Teknolojiler (Öneri)
*   Python 3.x
*   Google Gemini API client kütüphanesi
*   Web scraping için: `requests`, `BeautifulSoup4`, `lxml`. Daha karmaşık siteler için `Playwright` veya `Selenium`.
*   Veritabanı bağlantısı için: `psycopg2-binary` veya `SQLAlchemy`.
*   Zamanlama için: `APScheduler` veya işletim sistemi cron'u.
*   Veri işleme için: `pandas` (opsiyonel).

## 6. Mentor ile Tartışılacak Ana Konular (Özet)
**Python AI Servisi:**
    *   Dinamik "hikaye/özet" modellemesi (`analyzed_summary_outputs` tablo yapısı, ilişkili haberlerin ve kategorilerin saklanması).
    *   Python ve Spring Boot arasındaki potansiyel bildirim mekanizmaları.

Bu rapor, projenin mevcut durumunu ve gelecek planlarını kapsamlı bir şekilde özetlemektedir.