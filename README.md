# Summary Finance

https://summaryfinance.me/

Finans haberleri toplama, analiz etme ve özet çıkarma uygulaması.

## Proje Yapısı

Bu proje iki ana bileşenden oluşmaktadır:

1. **Spring Boot Backend**: Haber toplama, veritabanı yönetimi ve API sunumu
2. **Python AI Service**: Haber analizi ve özet çıkarma işlemleri

## Kurulum

### Spring Boot Uygulaması
1. `application.properties.example` dosyasını `application.properties` olarak kopyalayın
2. Veritabanı bilgilerinizi ve API anahtarlarınızı güncelleyin
3. Maven ile projeyi derleyin: `mvn clean install`
4. Uygulamayı başlatın: `mvn spring-boot:run`

### Python AI Service
1. `.env_template` dosyasını `.env` olarak kopyalayın
2. Veritabanı bilgilerinizi güncelleyin
3. Gereksinimleri yükleyin: `pip install -r requirements.txt`
4. Servisi başlatın: `uvicorn main:app --reload`

## Özellikler

- NYTimes ve Guardian kaynaklarından günlük finans haberleri toplama
- Kategori bazlı filtreleme 
- AI-tabanlı haber analizi ve özet çıkarma
- Günlük haber özetleri oluşturma

## Teknoloji Yığını

- **Backend**: Java 17, Spring Boot, PostgreSQL
- **AI Service**: Python, FastAPI, newspaper3k
- **API**: RESTful endpoints
