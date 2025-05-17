# Kapsamlı Proje Dokümantasyonu: Akıllı Finans Haberleri Analiz Platformu

**Proje Referans Kodu:** SFINX-001 (SummaryFinance-Extended)
**Belge Sürümü:** 1.1
**Son Güncelleme:** 11 Mayıs 2025

## Bölüm 1: Projeye Giriş ve Hedefler

### 1.1. Vizyon
Finansal piyasalar ve küresel ekonomi hakkında bilgi edinme sürecini dönüştürerek, kullanıcılara farklı kaynaklardan gelen karmaşık haber verilerini sentezlenmiş, analiz edilmiş ve eyleme geçirilebilir içgörülerle sunan lider bir platform olmak.

### 1.2. Misyon
Gelişmiş yapay zeka (özellikle Google Gemini) ve veri işleme teknikleri kullanarak, çeşitli haber kaynaklarından toplanan finans ve ilişkili konulardaki haberleri otomatik olarak analiz etmek, haberler arası gizli bağlantıları ve temaları ortaya çıkarmak, dinamik olarak "hikaye" tabanlı özetler üretmek ve bu özetleri kullanıcıların kolayca erişebileceği, anlayabileceği ve kendi kararlarında kullanabileceği bir formatta sunmak.

### 1.3. Çözülen Temel Sorun
Modern dünyada bireyler ve profesyoneller, finansal kararlarını etkileyebilecek çok sayıda haber kaynağına maruz kalmaktadır. Bu kaynakları manuel olarak takip etmek, farklı açılardan sunulan bilgileri birleştirmek, olaylar arasındaki nedensellik veya korelasyon ilişkilerini kurmak ve büyük resme hakim olmak son derece zaman alıcı ve zordur. Platformumuz, bu bilgi bombardımanını anlamlı içgörülere dönüştürerek bu sorunu çözmeyi hedefler.

### 1.4. Hedef Kitle
*   Bireysel yatırımcılar
*   Finans profesyonelleri (analistler, portföy yöneticileri)
*   Ekonomi ve finans öğrencileri/akademisyenleri
*   Finansal piyasaları ve ekonomik gelişmeleri yakından takip etmek isteyen herkes

### 1.5. Projenin Ana Çıktıları ve Değer Önerisi
1.  **Dinamik Hikaye Özetleri:** Sadece bireysel haber özetleri değil, AI tarafından birbiriyle ilişkili olduğu tespit edilen haber gruplarından (farklı kaynak ve kategorilerden olabilen) oluşturulmuş, daha derinlemesine analiz ve sentez içeren "hikaye" tabanlı özetler.
2.  **Kategorize Edilmiş İçgörüler:** Üretilen her hikaye özetinin, önceden tanımlanmış genel uygulama kategorilerine (Finans, Siyaset, Teknoloji, Enerji, Makroekonomi, Mikroekonomi, Borsa, Tarım, Fintech vb.) AI tarafından atanması.
3.  **Periyodik Güncellemeler:** Başlangıçta günlük olarak yeni haberlerin çekilmesi ve yeni hikaye özetlerinin üretilmesi.
4.  **Kaynak İzlenebilirliği:** Her özetin hangi orijinal haberlere dayandığının belirtilmesi.
5.  **Zaman Tasarrufu ve Bilgi Verimliliği:** Kullanıcıların çok sayıda kaynağı manuel taramak yerine, sentezlenmiş ve analiz edilmiş bilgiye hızla ulaşmasını sağlamak.

## Bölüm 2: Sistem Mimarisi ve Teknolojileri

### 2.1. Makro Mimari
Proje, dağıtık bir mimariye sahip olup, ana bileşenleri şunlardır:
*   **Veri Toplama ve API Katmanı (Spring Boot - Java):** Harici haber API'lerinden periyodik olarak haber metadata'sını çeker, ön işleme yapar, tekilleştirir ve ana veri tabanına kaydeder. Ayrıca, işlenmiş özetleri frontend'e sunacak RESTful API'leri barındırır.
*   **Analiz ve Yapay Zeka Katmanı (Python Servisi):** Ana veri tabanından haber metadata'sını okur, URL'ler üzerinden haberlerin tam içeriğini web scraping ile çeker, Google Gemini API'sini kullanarak metin analizi, ilişkilendirme, gruplama ve özetleme yapar. Sonuçları (analiz edilmiş hikayeler, kategoriler, kaynak haber linkleri) veri tabanına yazar.
*   **Veritabanı Katmanı (PostgreSQL):** Hem ham haber metadata'sını hem de AI tarafından üretilen analiz/özet çıktılarını saklar.
*   **Frontend Katmanı (React/Next.js - Varsayılan):** Kullanıcı arayüzünü oluşturur ve Spring Boot API'leri üzerinden verileri gösterir. (Bu dokümanın odağı dışındadır.)

![Sistem Mimarisi Diyagramı - Buraya bir diyagram eklenebilir]

### 2.2. Teknoloji Yığını
*   **Backend (Spring Boot):**
    *   Dil: Java (JDK 17+)
    *   Framework: Spring Boot 3.x
    *   Asenkron İşlemler: Spring WebFlux, Project Reactor (`Flux`, `Mono`)
    *   Veritabanı Erişimi: Spring Data JPA, Hibernate
    *   HTTP İstemcisi: `WebClient`
    *   Build Aracı: Maven (veya Gradle)
    *   Yardımcı Kütüphaneler: Lombok, MapStruct, Jackson
*   **AI Servisi (Python):**
    *   Dil: Python 3.x
    *   AI Model: Google Gemini API (Vertex AI veya Google AI Studio üzerinden)
    *   Web Scraping: `requests`, `BeautifulSoup4`, `lxml` (gerekirse `Playwright`/`Selenium` daha karmaşık siteler için)
    *   Veritabanı Bağlantısı: `psycopg2-binary` (PostgreSQL için) veya `SQLAlchemy`
    *   Zamanlama: `APScheduler` veya işletim sistemi cron'u
    *   Veri İşleme: `pandas` (opsiyonel)
*   **Veritabanı:**
    *   PostgreSQL (JSONB ve `TEXT[]` gibi gelişmiş veri tipleri için tercih edilmiştir)
*   **Geliştirme/Test Veritabanı:**
    *   H2 In-Memory Database
*   **API Kaynakları (Başlangıç):**
    *   The New York Times Article Search API
    *   The Guardian Content API

## Bölüm 3: Veri Toplama Süreci (Spring Boot)

### 3.1. Zamanlama (`NewsScheduler`)
*   `@Scheduled` anotasyonu ile Spring Boot tarafından yönetilen bir zamanlayıcı.
*   **Sıklık:** Her gün, `application.properties` dosyasındaki `news.fetch.cron` ifadesi ile yapılandırılabilir bir saatte (örn. varsayılan olarak sabah 05:00) çalışır.
*   **Görev:** `NewsService.fetchAndSaveAllConfiguredNewsReactive()` metodunu tetikler.

### 3.2. `NewsService`
*   **Ana Akış (`fetchAndSaveAllConfiguredNewsReactive`):**
    1.  Hedef tarih aralığını belirler (son 24 saat).
    2.  `application.properties`'den her haber kaynağı (NYTimes, Guardian) için aktif kategori anahtarlarını (`app.nytimes.enabled.keys` vb.) ve bu anahtarlara karşılık gelen API'ye özgü filtre string'lerini (`nytimes.filter.KEY_ISMI` vb.) okur.
    3.  Tanımlı her `NewsSourceClient` için (NYTimes, Guardian):
        *   O client'a ait aktif kategori anahtarları listesi üzerinden `Flux.fromIterable().concatMap(..., 1)` kullanarak **her bir kategoriyi sıralı olarak** işler. `prefetch=1` ile bir kategori tamamen işlenmeden diğerine geçilmez.
        *   Her kategori için, `environment.getProperty()` ile API'ye özgü filtre string'ini alır.
        *   `client.fetchNewsByTopic(apiSpecificFilter, startDate, endDate)` metodunu çağırarak o kategori ve tarih aralığındaki haberleri içeren bir `Flux<NewsDTO>` alır.
        *   Bu `Flux<NewsDTO>`'nun sonuna, bir sonraki kategoriye geçmeden önce API kaynağına özel bir gecikme (`api.client.inter-topic.delay.XXX.ms`) eklenir. **Bu gecikme, client'ın `fetchNewsByTopic` metodundan dönen `Flux` tamamlandıktan sonra uygulanır.**
    4.  Farklı API kaynaklarından gelen (her biri kendi içinde kategorileri sıralı işlemiş olan) ana `Flux<NewsDTO>`'lar, **`Flux.concat()`** kullanılarak sıralı bir şekilde birleştirilir (önce Guardian'ın tüm kategorileri, arada bir genel kaynaklar arası gecikme, sonra NYTimes'ın tüm kategorileri). Bu, en hassas API olan NYTimes'a yüklenmeden önce diğer kaynakların bitmesini sağlar.
    5.  Birleştirilmiş ana akıştaki tüm `NewsDTO`'lar `.collectList()` ile tek bir listede toplanır.
    6.  Bu liste, `deduplicateAndSaveNews()` metoduna gönderilir.
    7.  İşlem sonucu (başarılı/hatalı/kaydedilen sayı) loglanır ve `Mono<Void>` döndürülür.
*   **Tekilleştirme ve Kaydetme (`deduplicateAndSaveNews`):**
    1.  Gelen `List<NewsDTO>`'dan URL'leri alır.
    2.  `NewsRepository.findExistingUrls()` ile veritabanında bu URL'lerden hangilerinin zaten var olduğunu tek bir sorguyla kontrol eder.
    3.  Sadece yeni olan DTO'ları `NewsMapper` ile `News` entity'sine dönüştürür.
    4.  Her `News` entity'si için `fetchedAt` zamanını ve **API'den gelen ham `section` bilgisini** atar.
    5.  `NewsRepository.saveAll()` ile veritabanına kaydeder. Bu işlem `Schedulers.boundedElastic()` üzerinde asenkron olarak çalışır.

### 3.3. `NewsSourceClient` Arayüzü ve İstemci Sınıfları
*   **`NewsSourceClient` Arayüzü:**
    *   `Flux<NewsDTO> fetchNewsByTopic(String resolvedApiFilter, LocalDate startDate, LocalDate endDate);`
    *   `String getSourceName();`
*   **`NYTimesClient` ve `GuardianClient` Implementasyonları:**
    *   Constructor'da `WebClient.Builder` enjekte alır ve kendi `WebClient` örneğini oluşturur.
    *   `fetchNewsByTopic` Metodu:
        1.  API anahtarı ve gelen `resolvedApiFilter` kontrol edilir.
        2.  `startDate` ve `endDate` API'nin beklediği string formatına çevrilir.
        3.  **Dinamik Sayfalama:** `Flux.range(startPage, maxPages).delayElements(Duration.ofMillis(requestDelayMillis)).concatMap(pageNumber -> fetchPageData(...), 1)` mantığı kullanılır.
            *   `startPage`: NYT için 0, Guardian için 1.
            *   `maxPages`: NYT için 100, Guardian için makul bir üst limit (örn. 50) veya API yanıtındaki `pages` değeri kullanılana kadar devam.
            *   `requestDelayMillis`: Her sayfa isteği arasında `application.properties`'den alınan (`api.client.delay.XXX.ms`) gecikme uygulanır.
            *   `fetchPageData` metodu, o sayfa için API isteği yapar.
        4.  `fetchPageData` Metodu:
            *   API isteği URL'sini (filtre, tarihler, sayfa numarası, sayfa boyutu ile) oluşturur.
            *   `webClient.get().uri(...).retrieve()` ile istek atar.
            *   `onStatus(status -> status.isError(), ...)` ile HTTP hatalarını yakalar, loglar ve sayfalama durdurma sinyalini (`continueFetching.set(false)`) aktif eder, `Mono.error()` fırlatır.
            *   Yanıtı (`bodyToMono(JsonNode.class)`) alır.
            *   Yanıtın yapısını kontrol eder (`response`, `docs`/`results` alanları var mı, boş mu?).
            *   **Sayfalama Durdurma:** Yanıt boşsa, `docs`/`results` boşsa veya Guardian için `currentPage >= totalPages` ise `continueFetching.set(false)` çağrılır.
            *   Yanıtın ilgili kısmını (`docs` veya `results`) `parseJsonResponseToNewsDTOFlux` metoduna gönderir.
            *   `onErrorResume(e -> ...)` ile sayfa bazlı hataları yakalar, loglar, `continueFetching.set(false)` yapar ve `Flux.empty()` döner.
        5.  `parseJsonResponseToNewsDTOFlux` Metodu:
            *   Gelen `JsonNode` (makale listesi) üzerinde döngüye girer.
            *   Her makale için `url`, `title`, `publicationDate` (doğru parse ederek), **API'den gelen ham `section_name`/`news_desk`/`sectionName`** ve `source` (sabit değer) bilgilerini alarak bir `NewsDTO` oluşturur.
            *   Oluşturulan `NewsDTO`'ları `Flux.fromIterable()` ile emit eder.
        6.  Ana `fetchNewsByTopic` akışının sonunda `.takeWhile(newsDTO -> continueFetching.get())` ile, `continueFetching` bayrağı `false` olduğunda tüm akış kesilir.

## Bölüm 4: Veritabanı Tasarımı ve Yönetimi (PostgreSQL)

### 4.1. Tablolar ve İlişkiler
*   **`news` Tablosu:**
    *   `id`: `BIGSERIAL` (PK)
    *   `title`: `TEXT NOT NULL`
    *   `url`: `TEXT NOT NULL UNIQUE`
    *   `publication_date`: `TIMESTAMP WITH TIME ZONE NOT NULL`
    *   `section`: `VARCHAR(255) NOT NULL` (API'den gelen ham kategori/bölüm adı)
    *   `source`: `VARCHAR(255) NOT NULL` (Örn: "The New York Times", "The Guardian")
    *   `fetched_at`: `TIMESTAMP WITH TIME ZONE NOT NULL`
    *   *İndeksler:* `url` (unique), `publication_date`, `section`, `source`.
*   **`analyzed_summary_outputs` Tablosu:**
    *   `id`: `BIGSERIAL` (PK)
    *   `story_title`: `TEXT` (Opsiyonel, AI'ın temaya verdiği başlık)
    *   `summary_text`: `TEXT NOT NULL` (AI üretimi uzun analiz/özet metni)
    *   `publication_date`: `DATE NOT NULL` (Bu "hikayenin" referans aldığı tarih)
    *   `generated_at`: `TIMESTAMP WITH TIME ZONE NOT NULL`
    *   `assigned_categories`: `TEXT[] NOT NULL` (PostgreSQL string dizisi. AI'ın atadığı BİZİM standart genel uygulama kategorileri, örn: `{"FINANCE", "TECHNOLOGY"}`)
    *   *İndeksler:* `publication_date`, `assigned_categories` (GIN indeksi önerilir).
*   **`analyzed_news_links` Tablosu (Ara Tablo):**
    *   `id`: `BIGSERIAL` (PK)
    *   `summary_output_id`: `BIGINT NOT NULL REFERENCES analyzed_summary_outputs(id) ON DELETE CASCADE`
    *   `news_id`: `BIGINT NOT NULL REFERENCES news(id) ON DELETE CASCADE`
    *   `UNIQUE (summary_output_id, news_id)`
    *   *İndeksler:* `summary_output_id`, `news_id`.

### 4.2. Şema Yönetimi
*   Spring Boot uygulamasında `spring.jpa.hibernate.ddl-auto=update` ayarı kullanılacaktır. Bu, Hibernate'in veritabanı şemasını `@Entity` tanımlarına göre otomatik olarak oluşturmasını/güncellemesini sağlar.
*   Production ortamı için bu ayar `validate` veya `none` olarak değiştirilebilir ve şema değişiklikleri Flyway/Liquibase gibi araçlarla yönetilebilir (ileriki aşama).

### 4.3. Veritabanı Bağlantı Ayarları (`application.properties`)
*   PostgreSQL için:
    ```properties
    spring.datasource.url=jdbc:postgresql://localhost:5432/finans_haber_db
    spring.datasource.username=finans_user
    spring.datasource.password=finans_sifre
    spring.datasource.driver-class-name=org.postgresql.Driver
    spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect
    # spring.jpa.properties.hibernate.jdbc.lob.non_contextual_creation=true (TEXT için gerekebilir)
    ```
*   H2 (Test için):
    ```properties
    spring.datasource.url=jdbc:h2:mem:finanstestdb;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE
    spring.datasource.driverClassName=org.h2.Driver
    spring.datasource.username=sa
    spring.datasource.password=password
    spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
    ```

## Bölüm 5: Python AI Servisi Mimarisi (Genel Hatlar)

### 5.1. Ana Bileşenler
*   **Scheduler:** Günlük veya periyodik olarak analiz sürecini tetikler.
*   **Veritabanı Okuyucu:** `news` tablosundan işlenecek haberleri çeker.
*   **Web Scraper:** Haber URL'lerinden tam metin içeriğini alır.
*   **İçerik Temizleyici/Ön İşleyici:** Scraping ile alınan HTML'den saf metni çıkarır, gereksiz karakterleri temizler.
*   **AI Analiz Modülü (Gemini Entegrasyonu):**
    *   **Haber İlişkilendirme/Gruplama:** Birden fazla haber metnini Gemini'ye göndererek aralarındaki tematik bağlantıları, ortak konuları ve ilişkileri tespit eder. Haberleri dinamik olarak "hikaye kümelerine" ayırır.
    *   **Özet Üretme:** Her bir hikaye kümesi için, kümedeki haberleri baz alarak kapsamlı bir analiz ve özet metni üretir.
    *   **Kategori Atama:** Üretilen her hikaye özetini, önceden tanımlanmış genel uygulama kategorilerine (Finans, Siyaset vb.) atar. Bu, ya Gemini'ye doğrudan sorularak ya da özet metni üzerinden anahtar kelime/konu analiziyle yapılabilir.
*   **Veritabanı Yazıcı:** İşlenmiş `analyzed_summary_outputs` ve `analyzed_news_links` verilerini PostgreSQL'e yazar.

### 5.2. Gemini API Kullanımı (Örnek Senaryolar)
*   **İlişkilendirme:** "Aşağıdaki X haber metnini oku. Bu haberler arasında hangi ana temalar, olaylar veya varlıklar üzerinden bir ilişki kurulabilir? Bu ilişkileri ve ana temaları listele."
*   **Gruplanmış Özet:** "Belirlenen Y teması etrafında kümelenen şu Z adet haberin ortak ve farklı yönlerini vurgulayan, genel bir çıkarım sunan bir analiz ve özet metni oluştur."
*   **Kategorizasyon:** "Oluşturulan bu özet metni, aşağıdaki kategorilerden hangilerine en uygun düşmektedir: [Finans, Siyaset, Teknoloji...]? Her kategori için bir alaka skoru (0-1) ver."

### 5.3. Zorluklar
*   **Web Scraping:** Her sitenin yapısı farklıdır, dinamik içerik (JavaScript ile yüklenen) sorun olabilir. Scraper'ların bakımı gerekir. Anti-scraping önlemleriyle başa çıkmak gerekebilir.
*   **AI Prompt Mühendisliği:** Gemini'den istenen kalitede ve formatta çıktılar almak için etkili prompt'lar tasarlamak önemlidir.
*   **AI Maliyeti:** Çok sayıda haberin ve özetin Gemini API ile işlenmesi maliyetli olabilir. Optimizasyonlar (örn. sadece önemli haberleri işleme, özet uzunluğunu sınırlama) gerekebilir.
*   **Ölçeklenebilirlik:** Haber sayısı arttıkça scraping ve AI işleme süreleri uzayabilir. Asenkron görev kuyrukları (Celery vb.) ve paralel işleme düşünülebilir.

## Bölüm 6: Frontend API'leri (Spring Boot - `SummaryController`)

*   Frontend'in ihtiyaç duyacağı temel endpoint'ler:
    *   `GET /api/summaries/daily?date=YYYY-MM-DD`: Belirli bir gün için üretilmiş tüm "hikaye özetlerini" getirir.
    *   `GET /api/summaries/weekly?weekStartDate=YYYY-MM-DD`: Belirli bir hafta için üretilmiş tüm "hikaye özetlerini" getirir (veya tek bir haftalık bülten metni varsa onu).
    *   `GET /api/summaries?category=FINANCE&date=YYYY-MM-DD`: Belirli bir kategori ve tarih için özetleri getirir.
    *   `GET /api/summaries/{summaryId}`: Tek bir özetin detayını ve ilişkili haberlerini getirir.
*   Bu endpoint'ler `analyzed_summary_outputs` ve `analyzed_news_links` tablolarını sorgulayarak veri döndürür.
*   Sayfalama ve sıralama desteklenmelidir.

## Bölüm 7: Gelecek Geliştirmeler ve Potansiyel Özellikler
*   Kullanıcı bazlı kişiselleştirilmiş haber akışı ve özetler.
*   Duyarlılık analizi (Sentiment analysis) ve piyasa etkisi skorlaması.
*   Grafiksel veri görselleştirmeleri (trendler, ilişkiler).
*   Farklı dillerde haber desteği.
*   Kullanıcıların kendi API anahtarlarını ekleyebilmesi.
*   Mobil uygulama.
*   Gelişmiş bildirim sistemi.

Bu doküman, projenin mevcut anlayışını ve hedeflerini detaylı bir şekilde yansıtmaktadır. Mentor görüşmeleri ve geliştirme süreci boyunca güncellenecektir.