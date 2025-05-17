# Proje API Limitleri, Timeout Stratejileri ve Reaktif Akış Yönetimi Raporu

**Tarih:** 11 Mayıs 2025
**Proje:** Finans Haberleri Özetleyici

## 1. Amaç
Bu doküman, projemizde kullanılan harici haber API'lerinin (The New York Times ve The Guardian) bilinen rate limitlerini, sayfalama kısıtlamalarını ve bu limitlere uyum sağlamak için Spring Boot WebFlux (`WebClient`) tarafında uyguladığımız/uygulamayı planladığımız timeout, gecikme ve reaktif akış yönetimi stratejilerini özetlemektedir. Amaç, AI modelinin (Gemini) bu kısıtlamaları anlayarak daha gerçekçi ve uygulanabilir çözümler önermesine yardımcı olmaktır.

## 2. API Kaynakları ve Bilinen Limitleri

### 2.1. The New York Times (NYTimes) Article Search API
*   **Endpoint:** `https://api.nytimes.com/svc/search/v2/articlesearch.json`
*   **Rate Limit:**
    *   **Dakikada 10 istek.**
    *   **Günde 4.000 istek.**
    *   API dokümantasyonunda "her API çağrısı arasında en az 6 saniye beklemek önerilir" ifadesi bulunmaktadır.
*   **Sayfalama:**
    *   İstek başına maksimum **10 sonuç** döner.
    *   `page` parametresi (0'dan başlar) ile sayfalama yapılır.
    *   Tek bir filtre kombinasyonu için toplamda en fazla **1000 sonuç (100 sayfa)** alınabilir.
*   **Hata Kodu (Rate Limit Aşıldığında):** HTTP `429 Too Many Requests`.
*   **`Retry-After` Başlığı:** Dokümantasyonda net belirtilmese de, 429 yanıtlarında bu başlığın gelme ihtimali vardır ve dikkate alınmalıdır.
*   **Yanıt Süresi:** Genellikle birkaç saniye içinde yanıt verir, ancak sunucu yoğunluğuna göre değişebilir.
*   **Dönen Alanlar:** API, dönen alanları kısıtlamak için `fl` (field list) gibi bir parametre **sunmamaktadır**. İstek yapıldığında makaleyle ilgili tüm metadata (başlık, snippet, URL, desk, section_name, tarih vb.) döner.

### 2.2. The Guardian Content API
*   **Endpoint:** `https://content.guardianapis.com/search`
*   **Rate Limit (Geliştirici Katmanı):**
    *   **Saniyede 12 istek.**
    *   **Günde 5.000 istek.**
*   **Sayfalama:**
    *   Varsayılan olarak istek başına 10 sonuç döner.
    *   `page-size` parametresi ile bu sayı artırılabilir (örn. 50, maksimum ~200'e kadar çıkabilir). Bizim implementasyonumuzda **sayfa başına 50 sonuç** hedeflenmektedir.
    *   `page` parametresi (1'den başlar) ile sayfalama yapılır.
    *   API yanıtı, `response.total` (toplam sonuç) ve `response.pages` (toplam sayfa sayısı) bilgilerini içerir. Bu, sayfalama durdurma mantığı için kullanılır.
*   **Hata Kodu (Rate Limit Aşıldığında):** Muhtemelen HTTP `429 Too Many Requests` veya benzeri bir kod.
*   **Dönen Alanlar:** `show-fields` parametresi ile dönen alanlar kısıtlanabilir. Bizim projemizde **sadece temel metadata** (URL, başlık, tarih, section vb.) çekildiği için bu parametre şimdilik kullanılmamaktadır (yanıt boyutunu optimize etmek için ileride değerlendirilebilir).

## 3. Uygulanan/Planlanan Timeout ve Gecikme Stratejileri (Spring Boot WebClient)

### 3.1. Genel HTTP İstek Timeout (Spring MVC Async)
*   `application.properties` dosyasında `spring.mvc.async.request-timeout` ile ayarlanır.
*   Bu, `/api/news/fetch-reactive` gibi bir endpoint'e yapılan isteğin tamamlanması için tanınan toplam süredir.
*   **Mevcut Değer (Testler Sonrası):** Çok sayıda kategori ve API gecikmeleri nedeniyle bu değerin yüksek tutulması gerekmektedir (örn. **30-45 dakika** - `1800000`ms veya `2700000`ms).

### 3.2. `WebClient` Seviyesi Timeout'lar (Planlanan İyileştirme)
*   Merkezi bir `WebClient.Builder` konfigürasyonu (`WebClientConfig.java` içinde) ile veya her client için ayrı ayrı:
    *   **Bağlantı Zaman Aşımı (`ChannelOption.CONNECT_TIMEOUT_MILLIS`):** TCP bağlantısının kurulması için maksimum bekleme süresi (örn. **5000ms** - 5 saniye).
    *   **Yanıt Zaman Aşımı (`HttpClient.responseTimeout`):** İstek gönderildikten sonra sunucudan ilk yanıtın gelmesi için maksimum bekleme süresi (örn. **10000ms** - 10 saniye).
    *   **Okuma Zaman Aşımı (`ReadTimeoutHandler`):** Bağlantı kurulduktan sonra verinin tamamının okunması için süre (örn. **10000ms** - 10 saniye).
    Bu ayarlar, tek bir API isteğinin sonsuza kadar takılı kalmasını engeller.

### 3.3. API Kaynakları Arası Gecikme (`NewsService`)
*   Farklı API kaynaklarının (örn. önce tüm Guardian kategorileri, sonra tüm NYTimes kategorileri) işlenmesi arasına `application.properties`'den alınan `api.client.inter-source.delay.ms` (örn. **5-10 saniye**) kadar bir gecikme konulması planlanmaktadır (`Flux.concat` ve `Mono.delay` ile).

### 3.4. Kategoriler Arası Gecikme (`NewsService` içinde, her client için)
*   Her bir API kaynağı için, o kaynağa ait farklı kategorilerin (topic'lerin) API istekleri arasına `application.properties`'den alınan bir gecikme eklenmesi düşünülmektedir. Bu, `Flux.fromIterable(topicKeys).delayElements(Duration.ofMillis(interTopicDelayMs)).flatMap(...)` gibi bir yapıyla sağlanabilir.
    *   `api.client.inter-topic.delay.nytimes.ms`: Örn. **12000ms - 20000ms (12-20 saniye)**.
    *   `api.client.inter-topic.delay.guardian.ms`: Örn. **2000ms - 5000ms (2-5 saniye)**.

### 3.5. Sayfalar Arası Gecikme (Her `Client` Sınıfı İçinde)
*   Her bir API istemcisi (`NYTimesClient`, `GuardianClient`), bir kategori için sayfaları çekerken, her bir sayfa isteği arasında (`delayElements` veya `delaySequence` ile) `application.properties`'den alınan bir gecikme uygular.
    *   `api.client.delay.nytimes.ms`: **En az 7000ms (7 saniye)**, tercihen **10000ms - 15000ms (10-15 saniye)**. Bu, NYTimes'ın "dakikada 10 istek" limitine uymak için kritik.
    *   `api.client.delay.guardian.ms`: Örn. **1000ms - 2000ms (1-2 saniye)**.

## 4. Reaktif Akış Yönetimi ve Sayfalama

### 4.1. Dinamik Sayfalama
*   Her client, bir kategori ve tarih aralığı için API'nin izin verdiği veya veri döndürdüğü sürece sayfaları dinamik olarak çeker.
*   **NYTimes:** `Flux.range(0, MAX_PAGES_NYT)` ile başlar (max 100 sayfa).
*   **Guardian:** `Flux.range(1, MAX_ITERATION_LIMIT_GUARDIAN)` (örn. 50 sayfa) ile başlar.
*   **Sayfalama Durdurma Koşulları:**
    *   API'den boş bir sonuç listesi (`docs` veya `results` dizisi boş) geldiğinde.
    *   Guardian için API yanıtındaki `currentPage >= totalPages` koşulu sağlandığında.
    *   Bir API isteği sırasında timeout veya kurtarılamayan bir hata (örn. 401, 403) alındığında.
    *   Rate limit (429) hatası alındığında (retry mekanizması başarısız olursa).
    *   Bu durdurma, `AtomicBoolean continueFetching` ve `takeWhile` operatörü ile yönetilir.

### 4.2. Akış Birleştirme ve İşleme (`NewsService`)
*   Her client için, tüm kategorileri sıralı işleyen bir ana `Flux<NewsDTO>` oluşturulur (`Flux.fromIterable().delayElements().flatMap()`).
*   Bu ana client flux'ları, **`Flux.concat()`** kullanılarak sıralı bir şekilde birleştirilir (önce Guardian, sonra NYTimes). Bu, en hassas olan NYTimes API'sine yüklenmeden önce Guardian'ın tamamlanmasını sağlar.
*   Birleştirilmiş akıştaki tüm DTO'lar `.collectList()` ile toplanır.
*   Toplanan liste üzerinden tekilleştirme ve veritabanına kaydetme işlemleri yapılır.

### 4.3. Hata Yönetimi
*   **Client Seviyesi:**
    *   `onStatus` ile HTTP hataları (4xx, 5xx) yakalanır ve loglanır.
    *   `onErrorResume(e -> Flux.empty())` ile bir sayfa veya kategori için oluşan hata, o spesifik akışı sonlandırır ama genel haber çekme sürecini durdurmaz.
*   **Service Seviyesi:**
    *   Genel akışın sonunda `doOnError` ve `doFinally` ile genel hatalar loglanır ve işlemin durumu hakkında bilgi verilir.
*   **Retry Mekanizması (Planlanan İyileştirme):**
    *   Özellikle NYTimes için `429 Too Many Requests` ve genel 5xx sunucu hataları için `WebClient` seviyesinde `retryWhen(Retry.backoff(...).filter(...))` mekanizması eklenmesi şiddetle tavsiye edilir. `Retry-After` başlığı (eğer varsa) dikkate alınmalıdır.

## 5. Önemli Hususlar ve Riskler
*   **NYTimes Rate Limiti:** En büyük kısıtlayıcı faktör. Çok dikkatli gecikme ve istek yönetimi gerektirir. Günlük çekilecek toplam NYTimes kategorisi ve her kategoriden çekilecek maksimum sayfa sayısı, bu limite takılmamak için sınırlı tutulmalıdır.
*   **Toplam İşlem Süresi:** Çok sayıda kategori, sayfa ve aralarındaki gecikmeler, genel işlem süresini önemli ölçüde uzatabilir. `spring.mvc.async.request-timeout` değerinin bu süreye uygun olması gerekir.
*   **API Yanıt Yapısı Değişiklikleri:** API'ler zamanla değişebilir. `JsonNode` ile manuel parse etme, bu değişikliklere karşı kırılgandır. (İleride API'ye özel DTO'lara geçiş düşünülebilir.)
*   **"Invalid JSON" Hataları:** NYTimes'tan bazı kategoriler için alınan "invalid JSON structure or no 'docs' array" uyarılarının kaynağı araştırılmalıdır (API hatası mı, o an veri olmaması mı, filtreleme sorunu mu?).

Bu rapor, projenin mevcut timeout ve rate limit zorluklarını ve bunlara yönelik stratejileri kapsamaktadır.