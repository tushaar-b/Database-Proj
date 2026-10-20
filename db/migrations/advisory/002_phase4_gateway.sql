-- Phase 4 gateway additions; existing advisory data and tables are preserved.
ALTER TABLE surplus_snapshot
    ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_snapshot_user_evaluated_at
    ON surplus_snapshot (user_id, evaluated_at DESC);

ALTER TABLE recommendation_log
    ADD COLUMN IF NOT EXISTS batch_id UUID,
    ADD COLUMN IF NOT EXISTS shares INTEGER NOT NULL DEFAULT 1 CHECK (shares > 0),
    ADD COLUMN IF NOT EXISTS explanation TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_rec_user_batch
    ON recommendation_log (user_id, batch_id, generated_timestamp DESC);

CREATE TABLE IF NOT EXISTS recommendation_policy (
    user_id UUID PRIMARY KEY REFERENCES user_profile(user_id) ON DELETE CASCADE,
    capacity_multiplier NUMERIC(5,4) NOT NULL DEFAULT 1.0 CHECK (capacity_multiplier >= 0 AND capacity_multiplier <= 1),
    blocked_sectors TEXT[] NOT NULL DEFAULT '{}',
    reason TEXT NOT NULL DEFAULT 'No active risk breach.',
    triggering_portfolio_id UUID,
    triggering_metric TEXT,
    source_sequence BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applied_feedback_events (
    event_id UUID PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
