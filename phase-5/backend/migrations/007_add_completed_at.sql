-- Migration 007: Add completed_at column to tasks table
-- File: phase-5/backend/migrations/007_add_completed_at.sql
-- Purpose: Add completed_at timestamp column for tracking when tasks were completed
-- Backward Compatible: Existing tasks have NULL values for completed_at

BEGIN;

-- Add completed_at column (nullable, backward compatible)
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL;

-- Add comment for documentation
COMMENT ON COLUMN tasks.completed_at IS 'UTC timestamp when task was marked as completed. NULL for incomplete tasks or tasks that were never completed.';

COMMIT;

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name = 'completed_at';

