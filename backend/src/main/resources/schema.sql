-- Veritabanı oluşturma
CREATE DATABASE IF NOT EXISTS summary_finance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Kullanıcı oluşturma ve yetkilendirme
CREATE USER IF NOT EXISTS 'summary_finance'@'localhost' IDENTIFIED BY 'summary_finance';
GRANT ALL PRIVILEGES ON summary_finance.* TO 'summary_finance'@'localhost';
FLUSH PRIVILEGES;

USE summary_finance;

-- Haber makaleleri tablosu
CREATE TABLE IF NOT EXISTS news_articles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guardian_id VARCHAR(255) UNIQUE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    category VARCHAR(50),
    source_url VARCHAR(255),
    source_name VARCHAR(50),
    published_date DATETIME,
    created_at DATETIME,
    analysis_status VARCHAR(20) DEFAULT 'PENDING',
    summary TEXT,
    sentiment_score DOUBLE,
    key_points TEXT,
    main_topics VARCHAR(500),
    INDEX idx_status (analysis_status),
    INDEX idx_published (published_date),
    INDEX idx_category (category),
    INDEX idx_guardian (guardian_id)
);

-- Haber ilişkileri tablosu
CREATE TABLE IF NOT EXISTS news_relations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cluster_id VARCHAR(50),
    news_id BIGINT,
    relation_strength FLOAT,
    economic_impact_score FLOAT,
    created_at DATETIME,
    FOREIGN KEY (news_id) REFERENCES news_articles(id) ON DELETE CASCADE,
    INDEX idx_cluster (cluster_id),
    INDEX idx_news (news_id)
);

-- Haber özetleri tablosu
CREATE TABLE IF NOT EXISTS news_summaries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cluster_id VARCHAR(50) UNIQUE,
    summary TEXT,
    economic_analysis TEXT,
    created_at DATETIME,
    INDEX idx_cluster (cluster_id)
); 