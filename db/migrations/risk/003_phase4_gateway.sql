-- Phase 4 risk-side outbox and simulated rebalance idempotency.
-- Events are delivered at least once; Advisory DB applies event_id idempotently.
CREATE TABLE IF NOT EXISTS risk_feedback_state (
    user_id UUID PRIMARY KEY,
    policy_signature TEXT NOT NULL DEFAULT '',
    last_event_id UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_feedback_outbox (
    event_seq BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    portfolio_id UUID,
    triggering_metric TEXT,
    policy_signature TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_feedback_outbox_pending
    ON risk_feedback_outbox (event_seq) WHERE processed_at IS NULL;

CREATE TABLE IF NOT EXISTS rebalance_execution (
    idempotency_key UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    request_hash TEXT NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
