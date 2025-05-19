# SummaryFinance API Dokümantasyonu

Bu dokümantasyon, SummaryFinance projesindeki tüm API endpointlerini, parametrelerini, dönen değerlerini ve detaylı iş akışlarını açıklar.

## İçindekiler

1. [Haberler API](#haberler-api)
2. [İç API](#iç-api)
3. [SSE Bildirimleri API](#sse-bildirimleri-api)
4. [Sistem Genel İş Akışı](#sistem-genel-iş-akışı)

---

## Haberler API

Haber verileri için CRUD işlemlerini sağlayan API endpointleri. Bu endpointler, ham haber verilerinin yönetimi ve görüntülenmesi için kullanılır.

### GET `/api/news`

Tüm haberleri getirir. Frontend'de tüm haber listesini göstermek için kullanılır.

**İş Akışı:**
1. İstek alındığında `NewsService.getAllNews()` metodu çağrılır
2. `NewsRepository` aracılığıyla veritabanından tüm haberler getirilir
3. Veritabanı DTO nesnelerine dönüştürülür ve JSON formatında döndürülür

**Dönüş Değeri:**
- Status: `200 OK`
- Body: Haber DTO'larının listesi
```json
[
  {
    "id": "string",
    "title": "string",
    "content": "string",
    "publishedAt": "2025-05-18T10:00:00",
    "source": "string",
    "section": "string",
    "url": "string"
  }
]
```

### GET `/api/news/section/{section}`

Belirli bir kategorideki haberleri getirir. Kullanıcılar belirli kategorilere göre haberleri filtrelemek istediğinde kullanılır.

**İş Akışı:**
1. İstek, URL parametresi olarak kategori (section) bilgisi ile alınır
2. `NewsService.getNewsBySection(section)` metodu çağrılır
3. `NewsRepository` üzerinde kategori filtresi uygulanarak haberler getirilir
4. Sonuçlar DTO nesnelerine dönüştürülür ve döndürülür

**URL Parametreleri:**
- `section`: Haber kategorisi

**Dönüş Değeri:**
- Status: `200 OK`
- Body: Belirtilen kategorideki haber DTO'larının listesi

### GET `/api/news/date-range`

Belirli bir tarih aralığındaki haberleri getirir. Kullanıcılar belirli tarih aralığındaki haberleri görmek istediğinde kullanılır.

**İş Akışı:**
1. İstek, query parametreleri olarak başlangıç ve bitiş tarihi bilgileri ile alınır
2. Tarih parametreleri ISO 8601 formatından LocalDateTime nesnelerine dönüştürülür
3. `NewsService.getNewsByDateRange(start, end)` metodu çağrılır
4. `NewsRepository` üzerinde tarih aralığı filtresi uygulanarak haberler getirilir
5. Sonuçlar DTO nesnelerine dönüştürülür ve döndürülür

**Query Parametreleri:**
- `start`: Başlangıç tarihi (ISO 8601 formatında)
- `end`: Bitiş tarihi (ISO 8601 formatında)

**Örnek:**
```
GET /api/news/date-range?start=2025-05-01T00:00:00&end=2025-05-18T23:59:59
```

**Dönüş Değeri:**
- Status: `200 OK`
- Body: Belirtilen tarih aralığındaki haber DTO'larının listesi

### GET `/api/news/source/{source}`

Belirli bir kaynaktan gelen haberleri getirir. Kullanıcılar belirli haber kaynağından gelen haberleri görüntülemek istediğinde kullanılır.

**İş Akışı:**
1. İstek, URL parametresi olarak kaynak (source) bilgisi ile alınır
2. `NewsService.getNewsBySource(source)` metodu çağrılır
3. `NewsRepository` üzerinde kaynak filtresi uygulanarak haberler getirilir
4. Sonuçlar DTO nesnelerine dönüştürülür ve döndürülür

**URL Parametreleri:**
- `source`: Haber kaynağı

**Dönüş Değeri:**
- Status: `200 OK`
- Body: Belirtilen kaynaktan gelen haber DTO'larının listesi

### GET `/api/news/fetch-reactive`

Haberleri reaktif olarak getirip veritabanına kaydeder. Bu işlem asenkron olarak gerçekleşir ve manuel olarak haber toplama sürecini başlatmak için kullanılır.

**İş Akışı:**
1. İstek alındığında `NewsService.fetchAndSaveAllConfiguredNewsReactive()` metodu çağrılır
2. Bu metot, haberleri asenkron olarak toplamak için reaktif bir süreç başlatır
3. Metot hemen cevap döndürür (süreç başarıyla başlatıldı mesajı)
4. Arkaplanda, çeşitli haber kaynaklarından haberler çekilir
5. Toplanan haberler veritabanına kaydedilir
6. Kaydedilen haberler daha sonra AI servisi tarafından işlenir

**Dönüş Değeri:**
- Status: `200 OK` (başarılı başlatma)
- Body: `"Reactive news fetch process initiated successfully."`

veya

- Status: `500 Internal Server Error` (hata durumunda)
- Body: `"Reactive news fetch failed: <hata-mesajı>"`

---

## İç API

Python AI servisi gibi dahili servislerden gelen istekleri işleyen API endpointleri. Bu API, sistem dahilindeki servisler arasında veri alışverişi sağlar.

### POST `/api/internal/submit-ai-results`

Python AI servisinden gelen analiz edilmiş haber sonuçlarını kaydeder. AI servisi tarafından yapılan analiz sonuçlarını veritabanına kaydetmek için kullanılır.

**İş Akışı:**
1. Python AI servisi, haberleri gruplar ve analiz eder
2. Analiz sonuçları bu endpoint'e POST isteği ile gönderilir
3. `InternalApiController.submitAiResults()` metodu isteği alır
4. `ProcessedAiResultsService.saveAiResults()` metodu çağrılır
5. AI sonuçları veritabanına kaydedilir
6. Yeni kaydedilen özetler için `NotificationService` aracılığıyla SSE bildirimleri gönderilir
7. İşlemin sonucu yanıt olarak döndürülür

**İstek Body'si:**
```json
{
  "analyzedStories": [
    {
      "title": "string",
      "summaryText": "string",
      "categories": ["string"],
      "sentimentScore": 0.0,
      "keywords": ["string"],
      "relatedNewsIds": ["string"],
      "publishedAt": "2025-05-18T10:00:00"
    }
  ],
  "ungroupedNewsIds": ["string"]
}
```

**Dönüş Değeri (Başarılı):**
- Status: `200 OK`
- Body:
```json
{
  "success": true,
  "message": "AI işleme sonuçları başarıyla kaydedildi",
  "savedStoriesCount": 5,
  "ungroupedNewsCount": 2
}
```

**Dönüş Değeri (Başarısız):**
- Status: `400 Bad Request`
- Body:
```json
{
  "success": false,
  "message": "İşleme hatası: <hata-mesajı>"
}
```

---

## SSE Bildirimleri API

Server-Sent Events (SSE) aracılığıyla frontend istemcilere bildirim gönderen API endpointleri. Bu mekanizma, yeni özetler eklendiğinde kullanıcı arayüzünün gerçek zamanlı olarak güncellenmesini sağlar.

### GET `/api/summary-updates`

SSE akışını başlatan endpoint. İstemcilere yeni analiz özetleri hakkında bildirim gönderir.

**İş Akışı:**
1. Frontend istemci bu endpoint'e GET isteği gönderir ve `text/event-stream` formatında yanıt bekler
2. `SseNotificationController.streamSummaryUpdates()` metodu çağrılır
3. İstemciye hemen bir "connect" olayı gönderilir (bağlantı başarılı sinyali)
4. `NotificationService.getEventStream()` metodu çağrılarak bildirim akışı başlatılır
5. Bağlantı açık kalır ve istemci dinlemeye devam eder
6. Yeni özetler eklendiğinde (AI servisinden gelen sonuçlar kaydedildiğinde):
   a. `NotificationService` bir "new-summary" olayı yayınlar
   b. Bu olay tüm bağlı istemcilere iletilir
7. Düzenli aralıklarla (genellikle 30 saniyede bir) "keep-alive" olayları gönderilir
8. İstemci bağlantıyı kapattığında, sunucu tarafındaki kaynaklar temizlenir

**İstek Başlıkları:**
- `Accept: text/event-stream`

**Dönüş Değeri:**
- Content-Type: `text/event-stream`
- Body: SSE formatında bildirim akışı

**SSE Olay Türleri:**

1. **connect**: SSE bağlantısı kurulduğunda
```
event: connect
data: SSE stream'e bağlantı başarılı
```

2. **new-summary**: Yeni bir özet kaydedildiğinde
```
event: new-summary
data: {"id": "1", "title": "Örnek Haber Başlığı", "timestamp": "2025-05-18T10:00:00"}
```

3. **keep-alive**: Bağlantıyı canlı tutmak için
```
event: keep-alive
data: ping
```

**Kullanım Örneği (JavaScript):**
```javascript
const evtSource = new EventSource("/api/summary-updates");

evtSource.addEventListener("connect", (event) => {
  console.log("SSE bağlantısı kuruldu:", event.data);
});

evtSource.addEventListener("new-summary", (event) => {
  const summary = JSON.parse(event.data);
  console.log("Yeni özet alındı:", summary);
  // UI'ı güncelle
});

evtSource.addEventListener("keep-alive", (event) => {
  console.log("SSE bağlantısı canlı:", event.data);
});

evtSource.onerror = (error) => {
  console.error("SSE bağlantı hatası:", error);
  // Bağlantı hatası işleme
};
```

---

## Sistem Genel İş Akışı

SummaryFinance sistemi, birbirine entegre üç ana bileşenden oluşur: Spring Boot Backend, Python AI Servisi ve Frontend. Bu bileşenlerin nasıl etkileşimde bulunduğunu açıklayan genel iş akışı aşağıdadır:

### 1. Veri Toplama Süreci

1. Sistem, zamanlama yapılandırmasına göre veya manuel tetikleme (`/api/news/fetch-reactive` endpoint'i) ile haber toplama sürecini başlatır
2. Spring Boot backend, çeşitli haber kaynaklarından (API'ler, RSS beslemeleri vb.) haberleri çeker
3. Toplanan haberler veritabanına kaydedilir (`News` tablosu)

### 2. AI Analiz Süreci

1. Python AI servisi, düzenli aralıklarla veya tetiklemeyle çalışır
2. Python servisi, analiz için backend'den işlenmemiş haberleri çeker
3. AI servisi benzer haberleri gruplayıp, her grup için tek bir özet oluşturur
4. Duygu analizi, kategori tespiti ve anahtar kelime çıkarma gibi zeka işlemleri gerçekleştirilir
5. İşlenen sonuçlar backend'e gönderilir (`/api/internal/submit-ai-results` endpoint'i)

### 3. Sonuçların Kaydedilmesi ve Bildirim Süreci

1. Backend, AI servisinden gelen sonuçları veritabanına kaydeder
2. Sonuçlar kaydedildikten sonra, `NotificationService` aracılığıyla "new-summary" olayları yayınlanır
3. SSE bağlantısı açık olan tüm istemcilere bu bildirimler iletilir

### 4. Frontend Erişimi ve Güncelleme Süreci

1. Kullanıcılar web tarayıcıları aracılığıyla frontend'e erişir
2. Frontend yüklenirken, backend API'sine bağlanıp mevcut özetleri çeker
3. Aynı zamanda SSE bağlantısı kurulur (`/api/summary-updates` endpoint'i)
4. Kullanıcılar listeyi görüntüleyebilir, detayları inceleyebilir ve filtreleme yapabilir
5. Yeni özetler eklendiğinde, SSE kanalı üzerinden bildirim alınır ve liste otomatik olarak güncellenir

Bu iş akışı, kullanıcıların sayfayı yenilemeden en güncel finansal haber özetlerine erişmelerini sağlar. Backend ve AI servisi arka planda çalışmaya devam ederek yeni haberler toplar, analiz eder ve gerçek zamanlı güncellemeler sunar.

## Notlar

- Tüm API endpointleri için varsayılan içerik tipi `application/json`'dır (SSE hariç).
- Hata durumlarında, uygun HTTP durum kodları ve hata mesajları döndürülür.
- Tarihler ISO 8601 formatındadır (örn. `2025-05-18T10:00:00`).
- SSE bildirimleri gerçek zamanlı güncellemeler için kullanılır ve tarayıcı yenilemeye gerek kalmadan arayüzü günceller.
