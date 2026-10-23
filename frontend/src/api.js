// The development proxy keeps API requests and the host-only session cookie on
// the browser's origin. A custom direct API URL must use that same local hostname.
const configuredBase = (import.meta.env?.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
function resolveApiBase(base) {
  if (typeof window === 'undefined' || !/^https?:\/\//i.test(base)) return base;
  const url = new URL(base);
  const loopback = new Set(['localhost', '127.0.0.1', '[::1]']);
  if (loopback.has(url.hostname) && loopback.has(window.location.hostname)) {
    url.hostname = window.location.hostname;
  }
  return url.toString().replace(/\/$/, '');
}
const API_BASE = resolveApiBase(configuredBase);

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

// One controller owns identity, CSRF state, initialization and invalidation.
// No DOM events, component-local copies, localStorage or duplicate auth screens.
let csrfToken = '';
let generation = 0;
let snapshot = Object.freeze({ status: 'initializing', user: null, error: null, reason: null, generation, sessionKey: 0 });
const listeners = new Set();
let synchronization = null;
let authOperation = null;
let authOperationKind = null;
function publish(next) {
  snapshot = Object.freeze({ ...snapshot, error: null, ...next, generation });
  listeners.forEach((listener) => listener());
}
function anonymous(reason) {
  generation += 1;
  csrfToken = '';
  publish({ status: 'anonymous', user: null, reason });
}
function staleResponse() {
  return new ApiError('This request belongs to an earlier session. Please try again.', 0, { stale_session: true });
}
function acceptSession(result, expectedGeneration, newSession = false) {
  if (generation !== expectedGeneration) throw staleResponse();
  if (!result?.user?.user_id || !result.csrf_token) throw new ApiError('The API returned an incomplete session.', 502);
  generation += 1;
  csrfToken = result.csrf_token;
  const sessionKey = newSession || !snapshot.user || snapshot.user.user_id !== result.user.user_id ? generation : snapshot.sessionKey;
  publish({ status: 'authenticated', user: result.user, reason: null, sessionKey });
  return result;
}

export async function request(path, options = {}) {
  const requestGeneration = generation;
  const wasAuthenticated = Boolean(snapshot.user);
  const authEndpoint = ['/auth/login', '/auth/register', '/auth/logout', '/auth/me'].includes(path);
  const requiresSession = !authEndpoint && !['/health', '/'].includes(path);
  if (requiresSession && ['authenticating', 'signing-out'].includes(snapshot.status)) throw staleResponse();
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: 'include',
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(!['GET', 'HEAD', 'OPTIONS'].includes((options.method || 'GET').toUpperCase()) && csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    throw new ApiError('The IntelliVest API could not be reached. Check that the local backend is running.', 0, error);
  }

  const contentType = response.headers.get('content-type') || '';
  const payload = response.status === 204 ? null : contentType.includes('application/json') ? await response.json() : await response.text();
  // Discard old successes as well as failures before a caller can use them.
  if (requiresSession && requestGeneration !== generation) throw staleResponse();
  if (!response.ok) {
    if (response.status === 401 && requiresSession && wasAuthenticated && requestGeneration === generation) anonymous('expired');
    const detail = payload?.detail ?? payload;
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    throw new ApiError(message || `Request failed (${response.status})`, response.status, detail);
  }
  return payload;
}

function synchronizeSession() {
  // Strict Mode's repeated effects share this promise. Login/logout supersede
  // an in-flight check without allowing its eventual response to change state.
  if (authOperation) return authOperation.then(() => {
    if (!snapshot.user) throw new ApiError('Authentication required', 401);
    return { user: snapshot.user, csrf_token: csrfToken };
  });
  if (synchronization) return synchronization;
  const expectedGeneration = generation;
  const hadSession = Boolean(snapshot.user);
  const task = (async () => {
    try { return acceptSession(await request('/auth/me', { cache: 'no-store' }), expectedGeneration); }
    catch (error) {
      if (generation === expectedGeneration) {
        if (error.status === 401) anonymous(hadSession ? 'expired' : null);
        else if (hadSession) publish({ error });
        else publish({ status: 'error', user: null, error });
      }
      throw error;
    }
  })();
  synchronization = task;
  const cleanup = () => { if (synchronization === task) synchronization = null; };
  task.then(cleanup, cleanup);
  return task;
}

function authenticate(path, body) {
  // Serializing cookie-changing operations also prevents a late Set-Cookie
  // from an older login/logout from replacing a newer session in the browser.
  if (authOperation) return Promise.reject(new ApiError('An authentication request is already in progress.', 409));
  generation += 1;
  const expectedGeneration = generation;
  csrfToken = '';
  synchronization = null;
  publish({ status: 'authenticating', user: null, reason: null });
  const task = (async () => {
    try { return acceptSession(await request(path, json('POST', body)), expectedGeneration, true); }
    catch (error) {
      if (generation === expectedGeneration) publish({ status: 'anonymous', user: null });
      throw error;
    }
  })();
  authOperationKind = 'authenticate';
  authOperation = task;
  const cleanup = () => { if (authOperation === task) { authOperation = null; authOperationKind = null; } };
  task.then(cleanup, cleanup);
  return task;
}

function signOut() {
  if (authOperation) return authOperationKind === 'logout' ? authOperation : Promise.reject(new ApiError('An authentication request is already in progress.', 409));
  if (!snapshot.user) return Promise.resolve({ logged_out: true });
  generation += 1;
  const expectedGeneration = generation;
  synchronization = null;
  publish({ status: 'signing-out' });
  const task = (async () => {
    try {
      const result = await request('/auth/logout', { method: 'POST' });
      if (generation === expectedGeneration) anonymous('signed-out');
      return result;
    } catch (error) {
      if (generation === expectedGeneration) {
        if (error.status === 401) { anonymous('expired'); return { logged_out: true }; }
        // A failed logout has not revoked the server cookie. Keep the session
        // and token available, and display the failure rather than faking logout.
        publish({ status: 'authenticated', error });
      }
      throw error;
    }
  })();
  authOperationKind = 'logout';
  authOperation = task;
  const cleanup = () => { if (authOperation === task) { authOperation = null; authOperationKind = null; } };
  task.then(cleanup, cleanup);
  return task;
}

export const authSession = {
  getSnapshot: () => snapshot,
  subscribe: (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
  initialize: () => snapshot.status === 'initializing' || snapshot.status === 'error' ? synchronizeSession() : Promise.resolve(snapshot),
  clearError: () => publish({ error: null }),
};

const json = (method, body) => ({ method, body: JSON.stringify(body) });
const id = (value) => encodeURIComponent(value);

async function recommendationRequest(path, options, action) {
  try { return await request(path, options); }
  catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      const message = typeof error.detail === 'string' && error.detail.startsWith('Risk feedback is still synchronizing.')
        ? 'Risk feedback is still synchronizing. Please retry shortly; your saved recommendations are retained.'
        : `Recommendations could not be ${action}. Please retry; your saved recommendations are retained.`;
      throw new ApiError(message, error.status);
    }
    throw error;
  }
}

export const api = {
  getStockIntelligence: (ticker, options = {}) => {
    const params = new URLSearchParams(Object.entries(options).filter(([, value]) => value));
    return request(`/intelligence/stocks/${id(ticker)}?${params}`);
  },
  refreshPrices: () => request('/intelligence/refresh', { method: 'POST' }),
  getMarketQuotes: () => request('/intelligence/quotes'),
  register: (body) => authenticate('/auth/register', body),
  login: (body) => authenticate('/auth/login', body),
  currentUser: synchronizeSession,
  logout: signOut,
  getUser: (userId) => request(`/users/${id(userId)}`),
  updateUser: (userId, body) => request(`/users/${id(userId)}`, json('PATCH', body)),
  updateRiskTolerance: (userId, tier) => request(`/users/${id(userId)}/risk-tolerance`, json('PUT', { risk_tolerance_tier: tier })),
  getOnboardingProgress: (userId) => request(`/users/${id(userId)}/onboarding`),
  updateOnboardingProgress: (userId, step) => request(`/users/${id(userId)}/onboarding`, json('PUT', { step })),
  getSummary: (userId) => request(`/cashflow/${id(userId)}/summary`),
  evaluateCashflow: (userId, reserve) => request(`/cashflow/${id(userId)}/evaluate`, json('POST', { liquid_safety_reserve: reserve })),
  getIncome: (userId) => request(`/cashflow/${id(userId)}/income`),
  addIncome: (userId, body) => request(`/cashflow/${id(userId)}/income`, json('POST', body)),
  updateIncome: (incomeId, body) => request(`/cashflow/income/${id(incomeId)}`, json('PUT', body)),
  deleteIncome: (incomeId) => request(`/cashflow/income/${id(incomeId)}`, { method: 'DELETE' }),
  getExpenses: (userId) => request(`/cashflow/${id(userId)}/expenses`),
  addExpense: (userId, body) => request(`/cashflow/${id(userId)}/expenses`, json('POST', body)),
  updateExpense: (expenseId, body) => request(`/cashflow/expenses/${id(expenseId)}`, json('PUT', body)),
  deleteExpense: (expenseId) => request(`/cashflow/expenses/${id(expenseId)}`, { method: 'DELETE' }),
  getRecommendations: (userId) => recommendationRequest(`/recommendations/${id(userId)}`, undefined, 'loaded'),
  generateRecommendations: (userId) => recommendationRequest(`/recommendations/${id(userId)}/generate`, { method: 'POST' }, 'updated'),
  decideRecommendation: (userId, recommendationId, decision) => recommendationRequest(`/recommendations/${id(userId)}/${id(recommendationId)}/decision`, json('POST', { decision }), 'confirmed'),
  getPortfolios: (userId) => request(`/portfolios?user_id=${id(userId)}`),
  createPortfolio: (body) => request('/portfolios', json('POST', body)),
  getPortfolio: (portfolioId) => request(`/portfolios/${id(portfolioId)}`),
  updatePortfolio: (portfolioId, body) => request(`/portfolios/${id(portfolioId)}`, json('PATCH', body)),
  deletePortfolio: (portfolioId) => request(`/portfolios/${id(portfolioId)}`, { method: 'DELETE' }),
  getHoldings: (portfolioId) => request(`/portfolios/${id(portfolioId)}/holdings`),
  getSecurities: (query = '') => request(`/portfolios/securities${query ? `?q=${encodeURIComponent(query)}` : ''}`),
  addHolding: (portfolioId, body) => request(`/portfolios/${id(portfolioId)}/holdings`, json('POST', body)),
  updateHolding: (portfolioId, securityId, body) => request(`/portfolios/${id(portfolioId)}/holdings/${id(securityId)}`, json('PUT', body)),
  removeHolding: (portfolioId, securityId) => request(`/portfolios/${id(portfolioId)}/holdings/${id(securityId)}`, { method: 'DELETE' }),
  getRisk: (portfolioId) => request(`/portfolios/${id(portfolioId)}/risk`),
  getAlerts: (portfolioId) => request(`/alerts${portfolioId ? `?portfolio_id=${id(portfolioId)}` : ''}`),
  resolveAlert: (alertId) => request(`/alerts/${id(alertId)}/resolve`, { method: 'PATCH' }),
};

export { API_BASE };
