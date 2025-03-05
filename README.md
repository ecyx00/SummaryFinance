# SummaryFinance

Finans ve ekonomi haberlerini toplayan, analiz eden ve yapay zeka destekli özetler sunan bir web platformu.

## Proje Hakkında

SummaryFinance, The Guardian gibi güvenilir kaynaklardan ekonomi ve finans haberlerini otomatik olarak toplar, bunları Google Gemini API kullanarak analiz eder ve kullanıcıların haberleri daha verimli bir şekilde anlamalarını sağlayan özetler sunar. Platform, ayrıca ilişkili haberler arasında bağlantılar kurarak kullanıcıların daha geniş ekonomik trendleri ve etkileri anlamalarına yardımcı olur.

## Özellikler

- **Otomatik Haber Toplama**: The Guardian API kullanarak güncel ekonomi ve finans haberlerini otomatik olarak toplama
- **AI Destekli Analiz**: Google Gemini API ile haberlerin içeriğini analiz etme ve önemli bilgileri çıkarma
- **Haberleri Özetleme**: Uzun haberlerin yapay zeka ile oluşturulmuş özet versiyonlarını sunma
- **İlişki Analizi**: Farklı haberler arasındaki bağlantıları tespit ederek ilişkili haberleri gruplama
- **Finansal Etki Analizi**: Haberlerin potansiyel ekonomik etkilerini değerlendirme
- **Kategori Filtreleme**: Haberleri kategorilere göre filtreleme
- **Kaynak Bağlantıları**: Orijinal haber kaynaklarına doğrudan erişim

## Teknoloji Yığını

### Backend
- **Java 17**
- **Spring Boot 3.x**
- **MySQL 8.0** (Veritabanı)
- **Maven** (Bağımlılık yönetimi)
- **JPA / Hibernate** (ORM)

### AI Servisi
- **Python 3.9+**
- **Google Gemini API** (Metin analizi ve üretimi)
- **The Guardian API** (Haber kaynağı)
- **Requests** (HTTP istekleri)
- **BeautifulSoup** (HTML parsing)

### Frontend
- **React** (Temel UI kütüphanesi)
- **TailwindCSS** (Stil)

**Not**: Projenin mevcut aşamasında backend ve AI servisi geliştirmelerine öncelik verilmektedir. Frontend geliştirmeleri daha sonraki aşamalarda detaylandırılacaktır.

## Proje Yapısı

```
SummaryFinance/
├── backend/                  # Spring Boot backend
│   ├── src/main/java/com/summaryfinance/backend/
│   │   ├── config/           # Konfigürasyon sınıfları
│   │   ├── controller/       # REST API controller'ları
│   │   ├── dto/              # Data transfer nesneleri
│   │   ├── exception/        # Özel istisna sınıfları
│   │   ├── model/            # Veritabanı varlık sınıfları
│   │   ├── repository/       # Spring Data JPA repo'ları
│   │   ├── service/          # İş mantığı servisleri
│   │   │   └── newsfetcher/  # Haber toplama servisleri
│   │   └── BackendApplication.java
│   └── src/main/resources/   # Yapılandırma ve statik kaynaklar
├── ai-service/               # Python AI servisi
│   ├── api_client.py         # API istemci sınıfı
│   ├── news_service.py       # Ana haber servisi
│   ├── news_agents/          # AI ajanları
│   │   ├── news_reader_agent.py
│   │   ├── news_relation_agent.py
│   │   └── news_summary_agent.py
│   └── requirements.txt      # Python bağımlılıkları
└── frontend/                 # React frontend (geliştirme aşamasında)
```

## Kurulum Talimatları

### Önkoşullar
- Java 17 veya üzeri
- Maven 3.8+
- Python 3.9+
- Node.js 16+ ve npm
- MySQL 8.0+

### Ortam Hazırlama

1. **Veritabanı Kurulumu**
```sql
CREATE DATABASE summaryfinance;
CREATE USER 'summaryfinance'@'localhost' IDENTIFIED BY 'sifreburada';
GRANT ALL PRIVILEGES ON summaryfinance.* TO 'summaryfinance'@'localhost';
FLUSH PRIVILEGES;
```

2. **Konfigürasyon Dosyaları**

API anahtarları ve veritabanı kimlik bilgilerini içeren konfigürasyon dosyalarını oluşturun:

- `backend/src/main/resources/application.properties.example` dosyasını `application.properties` olarak kopyalayın ve güncelleyin
- `ai-service/.env.example` dosyasını `.env` olarak kopyalayın ve güncelleyin

### Backend Kurulumu

```bash
cd backend
./mvnw clean install
./mvnw spring-boot:run
```

### AI Service Kurulumu

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
pip install -r requirements.txt
python news_service.py
```

### Frontend Kurulumu

```bash
cd frontend
npm install
npm start
```

## API Endpoint'leri

### Haber Endpoint'leri

- `GET /api/v1/news/latest` - En son haberleri getir
- `GET /api/v1/news/{id}` - Belirli bir haberi getir
- `GET /api/v1/news/category/{category}` - Kategoriye göre haberleri getir

### Ajan Endpoint'leri

- `POST /api/v1/agent/fetchNews` - The Guardian'dan yeni haberler getir
- `POST /api/v1/agent/analyzeRelations` - Haber ilişkilerini analiz et
- `POST /api/v1/agent/generateSummaries` - Haber özetleri oluştur

## Güvenlik Notları

- API anahtarları gibi hassas bilgiler her zaman `.env` dosyalarında saklanmalı ve Git'e commit edilmemelidir
- Veritabanı şifreleri ve diğer kimlik bilgileri doğru bir şekilde korunmalıdır
- HTTPS protokolü üretim ortamında zorunludur
- Bağımlılıkları güvenlik açıkları için düzenli olarak güncelleyin

## Katkıda Bulunma

1. Bu repo'yu fork edin
2. Özellik dalı oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik: Açıklama'`)
4. Dalınıza push yapın (`git push origin yeni-ozellik`)
5. Pull Request açın

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - daha fazla detay için [LICENSE](LICENSE) dosyasına bakın.

## İletişim

Sorularınız veya önerileriniz mi var? [GitHub Issues](https://github.com/kullanici/SummaryFinance/issues) üzerinden iletişime geçebilirsiniz.
