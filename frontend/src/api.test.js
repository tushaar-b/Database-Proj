import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { ApiError, api, request, setCsrfToken } from './api.js';

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; setCsrfToken(''); });

test('registration uses cookie sessions and keeps CSRF only in memory', async () => {
  let captured;
  globalThis.fetch = async (url, options) => {
    captured = { url, options };
    return new Response(JSON.stringify({ user: { user_id: 'user-1' }, csrf_token: 'csrf-1' }), {
      status: 201,
      headers: { 'content-type': 'application/json' },
    });
  };

  const result = await api.register({ full_name: 'Asha', email: 'asha@example.com', password: 'long-enough-password', pan_hash: 'a'.repeat(64) });
  assert.equal(result.user.user_id, 'user-1');
  assert.equal(captured.url.endsWith('/auth/register'), true);
  assert.equal(captured.options.method, 'POST');
  assert.equal(captured.options.credentials, 'include');
  assert.equal(captured.options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(captured.options.body), { full_name: 'Asha', email: 'asha@example.com', password: 'long-enough-password', pan_hash: 'a'.repeat(64) });
  globalThis.fetch = async (_url, options) => {
    assert.equal(options.headers['X-CSRF-Token'], 'csrf-1');
    return new Response(null, { status: 204 });
  };
  await api.logout();
});

test('cash flow and portfolio readers use the configured API contracts', async () => {
  const urls = [];
  globalThis.fetch = async (url) => {
    urls.push(String(url));
    return new Response('[]', { status: 200, headers: { 'content-type': 'application/json' } });
  };
  await api.getIncome('user 1');
  await api.getExpenses('user 1');
  await api.getSecurities('TCS');
  assert.match(urls[0], /\/cashflow\/user%201\/income$/);
  assert.match(urls[1], /\/cashflow\/user%201\/expenses$/);
  assert.match(urls[2], /\/portfolios\/securities\?q=TCS$/);
});

test('API errors retain backend status and detail for visible UI messages', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Resolve the pending recommendation batch first' }), {
    status: 409,
    headers: { 'content-type': 'application/json' },
  });
  await assert.rejects(request('/recommendations/u/generate'), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 409);
    assert.equal(error.message, 'Resolve the pending recommendation batch first');
    return true;
  });
});

test('empty success and no-content responses are handled consistently', async () => {
  globalThis.fetch = async () => new Response(null, { status: 204 });
  assert.equal(await api.deleteIncome('income-1'), null);
});
