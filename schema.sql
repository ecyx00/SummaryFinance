-- news_db şeması
CREATE TABLE news_articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    guardian_id VARCHAR(255) UNIQUE,
    title TEXT,
    category VARCHAR(100),
    publication_date DATETIME,
    content TEXT,
    url VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE news_relations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cluster_id VARCHAR(255),
    news_id BIGINT,
    relation_strength FLOAT,
    economic_impact_score FLOAT,
    FOREIGN KEY (news_id) REFERENCES news_articles(id)
);

CREATE TABLE news_summaries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cluster_id VARCHAR(255),
    summary TEXT,
    economic_analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 