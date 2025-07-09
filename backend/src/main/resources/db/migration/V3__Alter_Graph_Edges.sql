-- graph_edges tablosuna updated_at sütunu ve unique constraint ekleme
ALTER TABLE graph_edges ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE graph_edges ADD CONSTRAINT uk_graph_edges_source_target UNIQUE (source_news_id, target_news_id);
