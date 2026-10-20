const API_BASE = (import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
let csrfToken = '';

export function setCsrfToken(token) { csrfToken = token || ''; }

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function request(path, options = {}) {
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
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    if (response.status === 401 && typeof window !== 'undefined') window.dispatchEvent(new Event('intellivest:session-expired'));
    const detail = payload?.detail ?? payload;
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    throw new ApiError(message || `Request failed (${response.status})`, response.status, detail);
  }
  return response.status === 204 ? null : payload;
}

const json = (method, body) => ({ method, body: JSON.stringify(body) });
const id = (value) => encodeURIComponent(value);

export const api = {
  register: async (body) => { const result = await request('/auth/register', json('POST', body)); setCsrfToken(result.csrf_token); return result; },
  login: async (body) => { const result = await request('/auth/login', json('POST', body)); setCsrfToken(result.csrf_token); return result; },
  currentUser: async () => { const result = await request('/auth/me'); setCsrfToken(result.csrf_token); return result; },
  logout: async () => { const result = await request('/auth/logout', { method: 'POST' }); setCsrfToken(''); return result; },
  getUser: (userId) => request(`/users/${id(userId)}`),
  updateUser: (userId, body) => request(`/users/${id(userId)}`, json('PATCH', body)),
  updateRiskTolerance: (userId, tier) => request(`/users/${id(userId)}/risk-tolerance`, json('PUT', { risk_tolerance_tier: tier })),
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
  getRecommendations: (userId) => request(`/recommendations/${id(userId)}`),
  generateRecommendations: (userId) => request(`/recommendations/${id(userId)}/generate`, { method: 'POST' }),
  decideRecommendation: (userId, recommendationId, decision) => request(`/recommendations/${id(userId)}/${id(recommendationId)}/decision`, json('POST', { decision })),
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
