-- V4__Add_Story_Tracking.sql
-- Migration to add story tracking and relationship capabilities
-- Part of Phase 3 implementation

-- 1. Update analyzed_stories table with new columns for story memory and tracking
ALTER TABLE analyzed_stories
    ADD COLUMN story_essence_text TEXT,
    ADD COLUMN story_context_snippets TEXT[],
    ADD COLUMN story_embedding_vector vector(384),
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN last_update_date TIMESTAMP WITH TIME ZONE;

-- Add comment to explain the purpose of these new columns
COMMENT ON COLUMN analyzed_stories.story_essence_text IS 'Condensed core essence/summary of the story (1-2 sentences)';
COMMENT ON COLUMN analyzed_stories.story_context_snippets IS 'Array of key snippets that define this story''s unique context';
COMMENT ON COLUMN analyzed_stories.story_embedding_vector IS 'Vector representation of story for similarity matching (384-dimensional)';
COMMENT ON COLUMN analyzed_stories.is_active IS 'Whether this story is still active/ongoing or archived';
COMMENT ON COLUMN analyzed_stories.last_update_date IS 'When this story was last updated with new developments';

-- 2. Create a new table for tracking relationships between stories
CREATE TABLE story_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_story_id BIGINT NOT NULL,
    target_story_id BIGINT NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    
    -- Foreign key constraints
    CONSTRAINT fk_source_story FOREIGN KEY (source_story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    CONSTRAINT fk_target_story FOREIGN KEY (target_story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    
    -- Avoid duplicate relationships
    CONSTRAINT unique_story_relationship UNIQUE (source_story_id, target_story_id, relationship_type)
);

-- Add comment to explain the purpose of this table
COMMENT ON TABLE story_relationships IS 'Tracks evolutionary and other relationships between different stories';

-- Add comments on columns
COMMENT ON COLUMN story_relationships.source_story_id IS 'ID of the source story (newer story in EVOLVED_FROM relationships)';
COMMENT ON COLUMN story_relationships.target_story_id IS 'ID of the target story (older story in EVOLVED_FROM relationships)';
COMMENT ON COLUMN story_relationships.relationship_type IS 'Type of relationship (e.g., EVOLVED_FROM, RELATED_TO, etc.)';
COMMENT ON COLUMN story_relationships.is_active IS 'Whether this relationship is still considered active';
COMMENT ON COLUMN story_relationships.created_at IS 'When this relationship was established';
COMMENT ON COLUMN story_relationships.created_by IS 'User or system component that established this relationship';

-- Create an index to speed up story relationship queries
CREATE INDEX idx_story_relationships_source_id ON story_relationships(source_story_id);
CREATE INDEX idx_story_relationships_target_id ON story_relationships(target_story_id);
CREATE INDEX idx_story_relationships_type ON story_relationships(relationship_type);
