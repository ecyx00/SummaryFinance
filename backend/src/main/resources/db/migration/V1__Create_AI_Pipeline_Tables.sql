-- Adding pgvector extension for vector support
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: news
-- Purpose: Main source data table containing raw news articles from external APIs
CREATE TABLE news (
    id BIGSERIAL NOT NULL,
    url VARCHAR(2048) NOT NULL,
    title VARCHAR(1024),
    source VARCHAR(255),
    publication_date TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (url)
);

-- Create indexes for the news table
CREATE INDEX idx_news_publication_date ON news (publication_date);
CREATE INDEX idx_news_source ON news (source);

-- Table: entities
-- Purpose: Store standardized entities extracted from news articles
CREATE TABLE entities (
    id BIGSERIAL NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    canonical_id VARCHAR(255),
    PRIMARY KEY (id),
    UNIQUE (name, type)
);

-- Table: article_entities (join table between news and entities)
-- Purpose: Link entities to their news articles
CREATE TABLE article_entities (
    news_id BIGINT NOT NULL,
    entity_id BIGINT NOT NULL,
    PRIMARY KEY (news_id, entity_id),
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Table: analyzed_stories
-- Purpose: Store finalized, enriched "evolving story" analyses produced by the AI pipeline
CREATE TABLE analyzed_stories (
    id BIGSERIAL NOT NULL,
    story_title VARCHAR(1024) NOT NULL,
    analysis_summary TEXT NOT NULL,
    story_date DATE,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    group_label VARCHAR(1024),
    connection_rationale TEXT,
    story_essence_text TEXT,
    story_context_snippets TEXT[],
    story_embedding_vector vector(384),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_update_date TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id)
);

-- Create indexes for the analyzed_stories table
CREATE INDEX idx_analyzed_stories_story_date ON analyzed_stories (story_date);
CREATE INDEX idx_analyzed_stories_embedding_vector ON analyzed_stories USING hnsw (story_embedding_vector vector_cosine_ops);

-- Table: story_news_link (join table between analyzed_stories and news)
-- Purpose: Link stories to their source news articles
CREATE TABLE story_news_link (
    story_id BIGINT NOT NULL,
    news_id BIGINT NOT NULL,
    PRIMARY KEY (story_id, news_id),
    FOREIGN KEY (story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
);

-- Table: story_relationships
-- Purpose: Manage temporal evolution and branching relationships between "evolving stories"
CREATE TABLE story_relationships (
    id BIGSERIAL NOT NULL,
    source_story_id BIGINT NOT NULL,
    target_story_id BIGINT NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    PRIMARY KEY (id),
    FOREIGN KEY (source_story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    FOREIGN KEY (target_story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE
);

-- Table: user_feedback
-- Purpose: Store user feedback on analysis reports
CREATE TABLE user_feedback (
    id BIGSERIAL NOT NULL,
    story_id BIGINT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    rating SMALLINT,
    is_helpful BOOLEAN,
    feedback_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    UNIQUE (story_id, ip_address),
    CHECK (rating >= 1 AND rating <= 5),
    CHECK (rating IS NOT NULL OR is_helpful IS NOT NULL)
);

-- Table: llm_interactions
-- Purpose: Log each call to the LLM API including input, output, and metadata
CREATE TABLE llm_interactions (
    id BIGSERIAL NOT NULL,
    request_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    task_type VARCHAR(255) NOT NULL,
    prompt_version VARCHAR(50),
    model_version VARCHAR(255),
    input_prompt TEXT,
    raw_output TEXT,
    parsed_output JSONB,
    token_usage JSONB,
    latency_ms INTEGER,
    story_id BIGINT,
    PRIMARY KEY (id),
    FOREIGN KEY (story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE
);

-- Create index for llm_interactions
CREATE INDEX idx_llm_interactions_task_type ON llm_interactions (task_type);

-- Table: ai_processing_log
-- Purpose: Log the journey, status, errors, and extracted intermediate data for each news article
CREATE TABLE ai_processing_log (
    id BIGSERIAL NOT NULL,
    news_id BIGINT NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'PENDING',
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    embedding_vector_id VARCHAR(255),
    embedding_model_version VARCHAR(255), -- Additional field required in the task
    PRIMARY KEY (id),
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
    UNIQUE (news_id)
);

-- Create index for ai_processing_log
CREATE INDEX idx_ai_processing_log_status ON ai_processing_log (status);

-- Table: graph_edges
-- Purpose: Log interaction scores and edges between news articles calculated in each analysis run
CREATE TABLE graph_edges (
    id BIGSERIAL NOT NULL,
    run_date DATE NOT NULL,
    source_news_id BIGINT NOT NULL,
    target_news_id BIGINT NOT NULL,
    semantic_score FLOAT,
    entity_score FLOAT,
    temporal_score FLOAT,
    total_interaction_score FLOAT,
    PRIMARY KEY (id),
    FOREIGN KEY (source_news_id) REFERENCES news(id) ON DELETE CASCADE,
    FOREIGN KEY (target_news_id) REFERENCES news(id) ON DELETE CASCADE
);

-- Create index for graph_edges
CREATE INDEX idx_graph_edges_run_date ON graph_edges (run_date);
