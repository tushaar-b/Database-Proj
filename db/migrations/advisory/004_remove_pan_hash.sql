-- Remove the unused PAN digest after application queries and schemas no longer
-- reference it. This migration preserves profile UUIDs and every related row.
-- Existing external backups or replicas are outside this migration's scope.
ALTER TABLE user_profile DROP COLUMN IF EXISTS pan_hash;
