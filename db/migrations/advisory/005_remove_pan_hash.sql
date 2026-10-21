-- Remove the unused PAN digest after application queries and models no longer
-- reference it. The column has no constraints or indexes; DROP COLUMN defaults
-- to RESTRICT, so PostgreSQL will stop if an undiscovered dependency exists.
-- User UUIDs and all related financial and risk records remain unchanged.
-- Existing database backups or replicas may retain older copies of this value;
-- apply the organization's existing backup-retention policy to those copies.
ALTER TABLE user_profile DROP COLUMN IF EXISTS pan_hash;
