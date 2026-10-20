-- Additive authentication storage. Existing profiles remain legacy accounts
-- until an administrator verifies ownership and supplies a password hash.
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS password_hash text;

CREATE TABLE IF NOT EXISTS auth_session (
    session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES user_profile(user_id) ON DELETE CASCADE,
    token_hash char(64) NOT NULL UNIQUE,
    csrf_token_hash char(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_auth_session_user ON auth_session(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_session_expiry ON auth_session(expires_at);

CREATE TABLE IF NOT EXISTS auth_login_attempt (
    attempt_id bigserial PRIMARY KEY,
    identifier_hash char(64) NOT NULL,
    client_hash char(64) NOT NULL,
    succeeded boolean NOT NULL DEFAULT false,
    attempted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_auth_attempt_identifier_time ON auth_login_attempt(identifier_hash, attempted_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_attempt_client_time ON auth_login_attempt(client_hash, attempted_at DESC);
