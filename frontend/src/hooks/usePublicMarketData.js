import { useEffect, useState } from 'react';
import { API_BASE } from '../api.js';

// This transport never sends a session cookie, changes auth state, or touches
// the private API client. In-flight reads are shared across Strict Mode mounts.
const cache = new Map();
const CACHE_MS = 60000;
function readMarket(path, force = false) {
  const cached = cache.get(path);
  if (!force && cached && cached.expires > Date.now()) return cached.promise;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 10000);
  const promise = fetch(`${API_BASE}/market${path}`, { credentials: 'omit', signal: controller.signal })
    .then(async (response) => {
      if (!response.ok) throw new Error('Stored research prices are unavailable. Please try again when the local market service is available.');
      const result = await response.json();
      if (result.classification !== 'illustrative_research') throw new Error('The market data classification is unavailable.');
      return result;
    }).finally(() => window.clearTimeout(timer));
  const entry = { promise, expires: Date.now() + CACHE_MS };
  cache.set(path, entry);
  promise.catch(() => { if (cache.get(path) === entry) cache.delete(path); });
  if (cache.size > 60) cache.delete(cache.keys().next().value);
  return promise;
}

export default function usePublicMarketData(path) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ path: null, status: 'loading', data: null, error: null });
  useEffect(() => {
    if (!path) return undefined;
    let active = true;
    setState({ path, status: 'loading', data: null, error: null });
    readMarket(path, attempt > 0).then((data) => {
      if (active) setState({ path, status: 'ready', data, error: null });
    }).catch((error) => {
      if (active) setState({ path, status: 'error', data: null, error: error.name === 'AbortError' ? 'The market service took too long to respond. Please retry.' : ['TypeError', 'SyntaxError'].includes(error.name) ? 'Stored research prices are unavailable. Check the local market service and retry.' : error.message });
    });
    return () => { active = false; };
  }, [path, attempt]);
  const current = state.path === path ? state : { status: 'loading', data: null, error: null };
  return { ...current, retry: () => setAttempt((value) => value + 1) };
}
