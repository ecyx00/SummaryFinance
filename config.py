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

config = {
    'guardian_api_key': 'your_guardian_api_key',
    'gemini_api_key': 'your_gemini_api_key',
    'db_config': {
        'host': 'localhost',
        'user': 'news_user',
        'password': 'password',
        'database': 'news_db'
    },
    'analysis_schedule': {
        'interval_minutes': 30
    },
    'categories': {
        'primary': ['business', 'money', 'technology'],
        'secondary': ['world', 'uk-news', 'environment', 
                     'global-development', 'science'],
        'opinion': ['guardian-view', 'columnists', 'opinion']
    }
} 