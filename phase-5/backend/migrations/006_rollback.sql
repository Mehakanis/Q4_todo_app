-- Rollback 006: Remove Phase V fields
-- File: phase-5/backend/migrations/006_rollback.sql
-- Purpose: Rollback Phase V schema changes (remove recurring tasks and reminders columns)
-- WARNING: This will DELETE all Phase V data (recurring patterns, reminders)

BEGIN;

-- Drop indexes first (PostgreSQL requires this before dropping columns)
DROP INDEX IF EXISTS idx_tasks_next_occurrence;
DROP INDEX IF EXISTS idx_tasks_reminder_at;

-- Drop Phase V columns
ALTER TABLE tasks
  DROP COLUMN IF EXISTS recurring_pattern,
  DROP COLUMN IF EXISTS recurring_end_date,
  DROP COLUMN IF EXISTS next_occurrence,
  DROP COLUMN IF EXISTS reminder_at,
  DROP COLUMN IF EXISTS reminder_sent;

COMMIT;

-- Verify rollback
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'tasks'
ORDER BY ordinal_position;

-- Verify indexes removed
SELECT
    indexname
FROM pg_indexes
WHERE tablename = 'tasks'
  AND indexname IN ('idx_tasks_next_occurrence', 'idx_tasks_reminder_at');
-- Expected: 0 rows (indexes should be deleted)
