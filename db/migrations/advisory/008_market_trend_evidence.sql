-- Additive research evidence only. No backfill, account/decision/price changes.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE public.recommendation_batch ADD COLUMN IF NOT EXISTS ranking_snapshot JSONB;
ALTER TABLE public.recommendation_log ADD COLUMN IF NOT EXISTS ranking_evidence JSONB;
COMMIT;
