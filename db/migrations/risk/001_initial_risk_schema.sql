-- ==============================================================================
-- IntelliVest Portfolio Risk Database Migration 001: Initial Schema
-- Target Database: risk_db
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- ENUM Types
-- ------------------------------------------------------------------------------
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tx_type') THEN
        CREATE TYPE tx_type AS ENUM ('BUY', 'SELL', 'AUTO_REBALANCE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'breached_metric') THEN
        CREATE TYPE breached_metric AS ENUM ('VAR_95_BREACH', 'SECTOR_HHI_EXCEEDED', 'VOLATILITY_SPIKE');
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- Table: PORTFOLIO
-- User investment portfolios, valuations, cash, and diversification limits
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PORTFOLIO (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    portfolio_name VARCHAR(255) NOT NULL,
    total_valuation NUMERIC(14, 2) NOT NULL DEFAULT 0.00 CHECK (total_valuation >= 0),
    cash_balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (cash_balance >= 0),
    target_hhi_limit NUMERIC(4, 3) NOT NULL DEFAULT 0.250 CHECK (target_hhi_limit > 0 AND target_hhi_limit <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON PORTFOLIO (user_id);

-- ------------------------------------------------------------------------------
-- Table: SECURITY_MASTER
-- Master registry of traded securities, sectors, exchanges, and volatility betas
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SECURITY_MASTER (
    security_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector_name VARCHAR(100) NOT NULL,
    exchange_code VARCHAR(20) NOT NULL DEFAULT 'NSE',
    beta_index NUMERIC(4, 2) DEFAULT 1.00
);

CREATE INDEX IF NOT EXISTS idx_security_sector ON SECURITY_MASTER (sector_name);

-- ------------------------------------------------------------------------------
-- Table: HOLDING
-- Current portfolio security positions and cost bases (Unique per portfolio+security)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS HOLDING (
    holding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES PORTFOLIO(portfolio_id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES SECURITY_MASTER(security_id) ON DELETE RESTRICT,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    average_buy_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (average_buy_price >= 0),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_portfolio_security UNIQUE (portfolio_id, security_id)
);

CREATE INDEX IF NOT EXISTS idx_holding_portfolio ON HOLDING (portfolio_id);

-- ------------------------------------------------------------------------------
-- Table: TRANSACTION_LEDGER
-- Immutable log of trade executions and automated compensating rebalances
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TRANSACTION_LEDGER (
    tx_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES PORTFOLIO(portfolio_id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES SECURITY_MASTER(security_id) ON DELETE RESTRICT,
    tx_type tx_type NOT NULL,
    units INT NOT NULL CHECK (units > 0),
    execution_price NUMERIC(10, 2) NOT NULL CHECK (execution_price > 0),
    tx_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tx_portfolio_time ON TRANSACTION_LEDGER (portfolio_id, tx_timestamp DESC);

-- ------------------------------------------------------------------------------
-- Table: DAILY_MARKET_QUOTE
-- Historical OHLCV market pricing (Unique per security+trade_date)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DAILY_MARKET_QUOTE (
    quote_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES SECURITY_MASTER(security_id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    close_price NUMERIC(10, 2) NOT NULL CHECK (close_price > 0),
    adjusted_close NUMERIC(10, 2) NOT NULL CHECK (adjusted_close > 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    CONSTRAINT uq_security_trade_date UNIQUE (security_id, trade_date)
);

-- Fast temporal query index (<10ms target for 30-day analytics)
CREATE INDEX IF NOT EXISTS idx_quote_temporal 
ON DAILY_MARKET_QUOTE (security_id, trade_date DESC);

-- ------------------------------------------------------------------------------
-- Table: REBALANCE_ALERT
-- Risk threshold breach alerts (VaR 95%, Volatility Spike, Sector HHI)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS REBALANCE_ALERT (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES PORTFOLIO(portfolio_id) ON DELETE CASCADE,
    drift_magnitude_pct NUMERIC(5, 2) NOT NULL,
    breached_metric breached_metric NOT NULL,
    resolved_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Partial index for active (unresolved) alerts
CREATE INDEX IF NOT EXISTS idx_active_alerts 
ON REBALANCE_ALERT (portfolio_id) 
WHERE resolved_flag = FALSE;

-- ------------------------------------------------------------------------------
-- Materialized View: mv_daily_sector_concentration
-- Precomputed sector valuations for Herfindahl-Hirschman Index (HHI)
-- (Definition placeholder to be populated and refreshed in analytical pipelines)
-- ------------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sector_concentration AS
SELECT 
    p.portfolio_id,
    sm.sector_name,
    COALESCE(SUM(h.quantity * h.average_buy_price), 0)::NUMERIC(14, 2) AS sector_valuation,
    COUNT(h.holding_id) AS asset_count,
    CURRENT_TIMESTAMP AS last_refreshed_at
FROM PORTFOLIO p
LEFT JOIN HOLDING h ON p.portfolio_id = h.portfolio_id
LEFT JOIN SECURITY_MASTER sm ON h.security_id = sm.security_id
GROUP BY p.portfolio_id, sm.sector_name
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_sector_conc_pk 
ON mv_daily_sector_concentration (portfolio_id, sector_name);
