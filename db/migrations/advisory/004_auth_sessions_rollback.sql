-- Optional rollback for an unused authentication deployment. This removes
-- session history and password hashes; export/retain account credentials first.
DROP TABLE IF EXISTS auth_login_attempt;
DROP TABLE IF EXISTS auth_session;
ALTER TABLE user_profile DROP COLUMN IF EXISTS password_hash;
