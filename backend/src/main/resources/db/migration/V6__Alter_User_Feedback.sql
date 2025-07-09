-- V6__Alter_User_Feedback.sql
-- Migration to fix data model inconsistencies in user_feedback table
-- Adds is_helpful column and modifies constraints for rating field

-- Add is_helpful column
ALTER TABLE user_feedback ADD COLUMN is_helpful BOOLEAN;

-- Make rating nullable
ALTER TABLE user_feedback ALTER COLUMN rating DROP NOT NULL;

-- Remove existing constraint
ALTER TABLE user_feedback DROP CONSTRAINT IF EXISTS check_rating_range;

-- Add new constraint ensuring at least one feedback type is provided
ALTER TABLE user_feedback ADD CONSTRAINT check_feedback_valid CHECK (
    (rating IS NOT NULL AND rating >= 1 AND rating <= 5) OR (is_helpful IS NOT NULL)
);

-- Add comment for new column
COMMENT ON COLUMN user_feedback.is_helpful IS 'Boolean feedback (helpful/not helpful) as an alternative to star rating';

-- Update table comment to reflect new functionality
COMMENT ON TABLE user_feedback IS 'Stores user feedback and ratings (star rating or helpful/not helpful) for story analysis reports';
