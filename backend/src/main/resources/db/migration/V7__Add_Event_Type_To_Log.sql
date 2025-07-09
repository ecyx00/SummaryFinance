-- Add event_type column to ai_processing_log table
-- This column will store the classified financial event type of news articles
ALTER TABLE ai_processing_log
ADD COLUMN event_type VARCHAR(100) NULL;

-- Create an index on the event_type column for faster queries
CREATE INDEX idx_ai_processing_log_event_type ON ai_processing_log (event_type);

-- Comment on the new column for documentation
COMMENT ON COLUMN ai_processing_log.event_type IS 'Classified financial event type (e.g. RATE_DECISION, INFLATION_DATA)';
