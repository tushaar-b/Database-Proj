-- Persist the reserve used for each evaluation without rewriting historical snapshots.
ALTER TABLE surplus_snapshot
    ADD COLUMN IF NOT EXISTS liquid_safety_reserve NUMERIC(12, 2);
