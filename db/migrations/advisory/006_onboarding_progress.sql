-- Persist only the current onboarding stage. Financial entries remain in their
-- existing tables and the account UUID remains the ownership key.
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS onboarding_step text;

-- Resume legacy accounts from the next stage supported by their saved Advisory
-- data. Portfolio choices remain discoverable through the authenticated API.
UPDATE user_profile up
SET onboarding_step = CASE
    WHEN EXISTS (SELECT 1 FROM income_stream i WHERE i.user_id = up.user_id) THEN
        CASE WHEN EXISTS (SELECT 1 FROM surplus_snapshot s WHERE s.user_id = up.user_id)
             THEN 'portfolio' ELSE 'expenses' END
    ELSE 'income'
END
WHERE onboarding_step IS NULL;

ALTER TABLE user_profile ALTER COLUMN onboarding_step SET DEFAULT 'income';
ALTER TABLE user_profile ALTER COLUMN onboarding_step SET NOT NULL;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_profile_onboarding_step_check'
          AND conrelid = 'user_profile'::regclass
    ) THEN
        ALTER TABLE user_profile ADD CONSTRAINT user_profile_onboarding_step_check
            CHECK (onboarding_step IN ('income','expenses','safety','evaluation','portfolio','analysis','dashboard'));
    END IF;
END $$;
