-- ai_processing_log tablosuna surprise_score sütunu ekle
ALTER TABLE ai_processing_log ADD COLUMN surprise_score FLOAT NULL;

-- Yeni eklenen sütun için açıklama
COMMENT ON COLUMN ai_processing_log.surprise_score IS 'Actual ve forecast değerler arasındaki normalize edilmiş fark (0.0-1.0 arası)';
