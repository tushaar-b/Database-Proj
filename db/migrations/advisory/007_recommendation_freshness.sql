-- Recommendation freshness support. Apply ONLY this file after schema review.
-- No UPDATE/DELETE/backfill of existing recommendations or decisions.
-- Existing legacy batch IDs and NULL fingerprints are deliberately preserved.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

ALTER TYPE public.recommendation_status ADD VALUE IF NOT EXISTS 'SUPERSEDED';

CREATE TABLE IF NOT EXISTS public.recommendation_batch (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profile(user_id) ON DELETE CASCADE,
    input_fingerprint CHAR(64),
    available_buffer NUMERIC(12,2),
    allocation_budget NUMERIC(12,2),
    outcome_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT recommendation_batch_identity UNIQUE (batch_id, user_id)
);

-- Add metadata columns for installations with an earlier batch-table version.
-- Do not change existing column types, defaults, nullability, or stored values.
ALTER TABLE public.recommendation_batch
    ADD COLUMN IF NOT EXISTS input_fingerprint CHAR(64),
    ADD COLUMN IF NOT EXISTS available_buffer NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS allocation_budget NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS outcome_reason TEXT;
ALTER TABLE public.recommendation_log ADD COLUMN IF NOT EXISTS batch_id UUID;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid='public.recommendation_batch'::regclass
          AND conname='recommendation_batch_identity'
    ) THEN
        ALTER TABLE public.recommendation_batch
            ADD CONSTRAINT recommendation_batch_identity UNIQUE (batch_id, user_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid='public.recommendation_log'::regclass
          AND conname='recommendation_log_batch_owner_fkey'
    ) THEN
        -- Enforce ownership for new batch references without rewriting or
        -- repairing legacy rows. Validate separately only after a legacy audit.
        ALTER TABLE public.recommendation_log
            ADD CONSTRAINT recommendation_log_batch_owner_fkey
            FOREIGN KEY (batch_id, user_id)
            REFERENCES public.recommendation_batch(batch_id, user_id) NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_recommendation_batch_user_created
    ON public.recommendation_batch(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rec_user_batch
    ON public.recommendation_log(user_id, batch_id, generated_timestamp DESC);
-- A fingerprint is intentionally not unique: reconsideration may create a new
-- batch for the same inputs after the configured review interval.
COMMIT;
