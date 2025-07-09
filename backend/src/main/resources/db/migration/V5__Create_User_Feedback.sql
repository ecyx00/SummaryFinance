-- V5__Create_User_Feedback.sql
-- Migration to add user feedback capabilities for story analysis reports
-- Part of Phase 4 implementation

-- Create a new table for user feedback on story analyses
CREATE TABLE user_feedback (
    id BIGSERIAL PRIMARY KEY,
    story_id BIGINT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    ip_address VARCHAR(45) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_feedback_story FOREIGN KEY (story_id) REFERENCES analyzed_stories(id) ON DELETE CASCADE,
    
    -- Ensure rating is between 1-5
    CONSTRAINT check_rating_range CHECK (rating >= 1 AND rating <= 5),
    
    -- Prevent multiple ratings from same IP for same story
    CONSTRAINT unique_ip_story_feedback UNIQUE (story_id, ip_address)
);

-- Add comment to explain the purpose of this table
COMMENT ON TABLE user_feedback IS 'Stores user feedback and ratings for story analysis reports';

-- Add comments on columns
COMMENT ON COLUMN user_feedback.story_id IS 'ID of the analyzed story being rated';
COMMENT ON COLUMN user_feedback.rating IS 'Rating value from 1 to 5 stars';
COMMENT ON COLUMN user_feedback.comment IS 'Optional comment provided with feedback';
COMMENT ON COLUMN user_feedback.ip_address IS 'IP address of the user submitting feedback (for rate limiting)';
COMMENT ON COLUMN user_feedback.created_at IS 'When this feedback was submitted';

-- Create indexes to speed up common queries
CREATE INDEX idx_feedback_story_id ON user_feedback(story_id);
CREATE INDEX idx_feedback_ip_address ON user_feedback(ip_address);
CREATE INDEX idx_feedback_created_at ON user_feedback(created_at);
