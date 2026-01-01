-- Migration 006: Add Phase V fields for recurring tasks and reminders
-- File: phase-5/backend/migrations/006_add_phase5_fields.sql
-- Purpose: Add nullable columns for Phase V features (recurring tasks, reminders)
-- Backward Compatible: Existing tasks have NULL values for new fields

BEGIN;

-- Add nullable columns (backward compatible with Phase II/III/IV tasks)
ALTER TABLE tasks
  ADD COLUMN recurring_pattern VARCHAR(500) NULL,
  ADD COLUMN recurring_end_date TIMESTAMP NULL,
  ADD COLUMN next_occurrence TIMESTAMP NULL,
  ADD COLUMN reminder_at TIMESTAMP NULL,
  ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE;

-- Add index on next_occurrence for fast queries by Recurring Task Service
-- Partial index: only index rows where next_occurrence IS NOT NULL
CREATE INDEX idx_tasks_next_occurrence
  ON tasks(next_occurrence)
  WHERE next_occurrence IS NOT NULL;

-- Add composite index on (reminder_at, user_id) for fast queries by Notification Service
-- Partial index: only index pending reminders (not yet sent)
CREATE INDEX idx_tasks_reminder_at
  ON tasks(reminder_at, user_id)
  WHERE reminder_at IS NOT NULL AND reminder_sent = FALSE;

-- Add column comments for documentation
COMMENT ON COLUMN tasks.recurring_pattern IS 'RRULE string (RFC 5545) or simplified pattern (e.g., FREQ=DAILY;INTERVAL=1). NULL for non-recurring tasks.';
COMMENT ON COLUMN tasks.recurring_end_date IS 'UTC timestamp when recurring should stop. NULL for infinite recurrence.';
COMMENT ON COLUMN tasks.next_occurrence IS 'UTC timestamp when next occurrence should be created. NULL for non-recurring tasks or completed recurring tasks.';
COMMENT ON COLUMN tasks.reminder_at IS 'UTC timestamp when reminder notification should be sent. NULL if no reminder scheduled.';
COMMENT ON COLUMN tasks.reminder_sent IS 'TRUE if reminder notification was sent. FALSE otherwise.';

COMMIT;

-- Verify migration
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
  AND column_name IN ('recurring_pattern', 'recurring_end_date', 'next_occurrence', 'reminder_at', 'reminder_sent')
ORDER BY ordinal_position;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'tasks'
  AND indexname IN ('idx_tasks_next_occurrence', 'idx_tasks_reminder_at');
