-- ==============================================================================
-- IntelliVest Advisory Database Migration 001: Initial Schema
-- Target Database: advisory_db
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- ENUM Types
-- ------------------------------------------------------------------------------
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_tolerance_tier') THEN
        CREATE TYPE risk_tolerance_tier AS ENUM ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'income_frequency') THEN
        CREATE TYPE income_frequency AS ENUM ('MONTHLY', 'YEARLY');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recommendation_status') THEN
        CREATE TYPE recommendation_status AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED');
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- Table: USER_PROFILE
-- Investor identity and risk profile tier
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS USER_PROFILE (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    risk_tolerance_tier risk_tolerance_tier NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- Table: INCOME_STREAM
-- Granular recurring income sources per user
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS INCOME_STREAM (
    income_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
    source_category VARCHAR(100) NOT NULL,
    gross_amount NUMERIC(12, 2) NOT NULL CHECK (gross_amount >= 0),
    frequency income_frequency NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- Table: EXPENSE_ITEM
-- Categorized user expenditures with mandatory/discretionary flag
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS EXPENSE_ITEM (
    expense_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    recurrence_interval VARCHAR(50) NOT NULL DEFAULT 'MONTHLY'
);

-- ------------------------------------------------------------------------------
-- Table: SURPLUS_SNAPSHOT
-- Historical evaluation of user investable surplus and safety reserve
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SURPLUS_SNAPSHOT (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
    total_income NUMERIC(12, 2) NOT NULL,
    total_expense NUMERIC(12, 2) NOT NULL,
    computed_surplus NUMERIC(12, 2) NOT NULL,
    investable_buffer NUMERIC(12, 2) NOT NULL,
    evaluated_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- ------------------------------------------------------------------------------
-- Table: RECOMMENDATION_LOG
-- Affordability-capped equity allocation recommendations
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS RECOMMENDATION_LOG (
    rec_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
    stock_ticker VARCHAR(20) NOT NULL,
    target_allocation_pct NUMERIC(5, 2) NOT NULL CHECK (target_allocation_pct >= 0 AND target_allocation_pct <= 100),
    recommended_amount NUMERIC(12, 2) NOT NULL CHECK (recommended_amount >= 0),
    status_state recommendation_status NOT NULL DEFAULT 'PENDING',
    generated_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_rec_user_status 
ON RECOMMENDATION_LOG (user_id, status_state, generated_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_income_user_id 
ON INCOME_STREAM (user_id);

CREATE INDEX IF NOT EXISTS idx_expense_user_id 
ON EXPENSE_ITEM (user_id);

CREATE INDEX IF NOT EXISTS idx_snapshot_user_date 
ON SURPLUS_SNAPSHOT (user_id, evaluated_date DESC);
