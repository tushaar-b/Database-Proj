import { spawnSync } from 'node:child_process';

export default function globalTeardown() {
  const script = `
import os, psycopg2
advisory = psycopg2.connect(os.environ['ADVISORY_DB_URL'])
risk = psycopg2.connect(os.environ['RISK_DB_URL'])
try:
    with advisory.cursor() as cur:
        cur.execute("SELECT user_id::text FROM user_profile WHERE email LIKE 'phase6-e2e-%@example.test'")
        users = [row[0] for row in cur.fetchall()]
    if users:
        with risk:
            with risk.cursor() as cur:
                cur.execute("SELECT event_id::text FROM risk_feedback_outbox WHERE user_id=ANY(%s::uuid[])", (users,))
                event_ids = [row[0] for row in cur.fetchall()]
                cur.execute("DELETE FROM portfolio WHERE user_id=ANY(%s::uuid[])", (users,))
                cur.execute("DELETE FROM risk_feedback_outbox WHERE user_id=ANY(%s::uuid[])", (users,))
                cur.execute("DELETE FROM risk_feedback_state WHERE user_id=ANY(%s::uuid[])", (users,))
        with advisory:
            with advisory.cursor() as cur:
                if event_ids:
                    cur.execute("DELETE FROM applied_feedback_events WHERE event_id::text=ANY(%s::text[])", (event_ids,))
                cur.execute("DELETE FROM user_profile WHERE user_id=ANY(%s::uuid[])", (users,))
finally:
    advisory.close()
    risk.close()
`;
  const result = spawnSync(process.env.INTELLIVEST_PYTHON || 'python3', ['-c', script], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(`Test record cleanup failed: ${result.stderr || result.error}`);
}
