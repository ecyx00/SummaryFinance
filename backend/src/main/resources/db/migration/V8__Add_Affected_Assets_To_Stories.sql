-- Add affected_assets column to analyzed_stories table
-- This column will store the list of financial assets potentially affected by the news
ALTER TABLE analyzed_stories
ADD COLUMN affected_assets TEXT[] NULL;

-- Create an index on the affected_assets column using GIN for array search optimization
CREATE INDEX idx_analyzed_stories_affected_assets ON analyzed_stories USING GIN (affected_assets);

-- Comment on the new column for documentation
COMMENT ON COLUMN analyzed_stories.affected_assets IS 'List of financial assets (e.g. EURUSD, AAPL) potentially affected by the news';
