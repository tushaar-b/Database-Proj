import { Suspense, lazy, useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowLeft, ArrowRight, ArrowUpRight, Bell, BriefcaseBusiness,
  Check, CircleHelp, CirclePlus, Eye, EyeOff, Gauge, LayoutDashboard, LoaderCircle,
  LogOut, Menu, RefreshCw, ShieldCheck, SlidersHorizontal, Sparkles, Wallet,
  X,
} from 'lucide-react';
import { api, ApiError } from './api.js';
import GuidedOnboarding from './GuidedOnboarding.jsx';

const HoldingsChart = lazy(() => import('./HoldingsChart.jsx'));
const INR = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
const NUM = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });
const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'cashflow', label: 'Cash flow', icon: Wallet },
  { id: 'recommendations', label: 'Recommendations', icon: Sparkles },
  { id: 'portfolios', label: 'Portfolios', icon: BriefcaseBusiness },
  { id: 'risk', label: 'Risk analytics', icon: Gauge },
  { id: 'alerts', label: 'Alerts', icon: Bell },
];

const money = (value) => value === null || value === undefined || value === '' ? '—' : INR.format(Number(value));
const number = (value, digits = 2) => value === null || value === undefined || value === '' ? '—' : Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits });
const percent = (value, digits = 2) => value === null || value === undefined ? '—' : `${number(Number(value) * 100, digits)}%`;
const dateLabel = (value) => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value)) : '—';
const errorMessage = (error) => error instanceof ApiError ? error.message : (error?.message || 'Something went wrong. Please try again.');

function MetricCard({ label, value, helper, icon: Icon, tone = 'blue', trend }) {
  return <article className={`metric-card tone-${tone}`}>
    <div className="metric-heading"><span>{label}</span><span className="metric-icon"><Icon size={18} /></span></div>
    <strong className="metric-value">{value}</strong>
    <div className="metric-foot"><span>{helper}</span>{trend && <span className="metric-trend">{trend}</span>}</div>
  </article>;
}

function PageHeading({ eyebrow, title, description, action }) {
  return <div className="page-heading">
    <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>
    {action && <div className="heading-action">{action}</div>}
  </div>;
}

function Notice({ notice, dismiss }) {
  if (!notice) return null;
  return <div className={`notice notice-${notice.type || 'error'}`} role="status">
    <span>{notice.message}</span><button className="icon-button" onClick={dismiss} aria-label="Dismiss message"><X size={16} /></button>
  </div>;
}

function EmptyState({ icon: Icon = CircleHelp, title, copy, action }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={21} /></span><strong>{title}</strong><p>{copy}</p>{action}</div>;
}

function LoadingState({ label = 'Loading your financial workspace…' }) {
  return <div className="loading-state"><LoaderCircle className="spin" size={22} />{label}</div>;
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [registrationStep, setRegistrationStep] = useState('account');
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' });
  const [visible, setVisible] = useState({ password: false, confirm: false });
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});
  const change = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const register = mode === 'register';
  function switchMode(next) { setMode(next); setRegistrationStep('account'); setErrors({}); }
  async function submit(event) {
    event.preventDefault(); setErrors({});
    if (register && registrationStep === 'account') {
      const next = {};
      if (!form.full_name.trim()) next.full_name = 'Enter your full name.';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = 'Enter a valid email address.';
      setErrors(next);
      if (!Object.keys(next).length) setRegistrationStep('password');
      return;
    }
    const next = {};
    if (!form.email.trim()) next.email = 'Enter your email address.';
    if (!form.password) next.password = 'Enter your password.';
    if (register && form.password.length < 12) next.password = 'Use at least 12 characters.';
    if (register && form.password !== form.confirm_password) next.confirm_password = 'Passwords do not match.';
    if (Object.keys(next).length) { setErrors(next); return; }
    setBusy(true);
    try {
      const result = register
        ? await api.register({ full_name: form.full_name.trim(), email: form.email.trim(), password: form.password })
        : await api.login({ email: form.email.trim(), password: form.password });
      onAuthenticated(result.user);
    } catch (issue) { setErrors({ form: errorMessage(issue) }); }
    finally { setBusy(false); }
  }
  const title = register ? (registrationStep === 'account' ? 'Let’s get to know you.' : 'Secure your account.') : 'Welcome back.';
  const description = register ? (registrationStep === 'account' ? 'We’ll start with a few details to set up your IntelliVest account.' : 'Choose a strong password to keep your financial workspace private.') : 'Sign in to continue to your personal financial workspace.';
  return <main className="auth-shell">
    <header className="auth-top"><Brand compact /><span className="local-only"><i />Private, local IntelliVest workspace</span></header>
    <section className="auth-content">
      <div className="auth-card">
        {register && <div className="auth-progress"><span className={registrationStep === 'account' ? 'active' : 'complete'} /><span className={registrationStep === 'password' ? 'active' : ''} /><small>{registrationStep === 'account' ? 'Step 1 of 2' : 'Step 2 of 2'} · Account setup</small></div>}
        <div className="auth-welcome-mark"><Activity size={22} /></div><p className="eyebrow">{register ? 'Create your IntelliVest account' : 'Investor workspace'}</p><h1>{title}</h1><p className="auth-description">{description}</p>
        {errors.form && <div className="wizard-error" role="alert">{errors.form}</div>}
        <form className="auth-form" onSubmit={submit} noValidate>
          {register && registrationStep === 'account' && <>
            <Field label="Full name"><input autoFocus autoComplete="name" maxLength="255" value={form.full_name} onChange={change('full_name')} aria-invalid={Boolean(errors.full_name)} placeholder="Your full name" />{errors.full_name && <small className="field-error">{errors.full_name}</small>}</Field>
            <Field label="Email address"><input type="email" autoComplete="email" maxLength="255" value={form.email} onChange={change('email')} aria-invalid={Boolean(errors.email)} placeholder="you@example.com" />{errors.email && <small className="field-error">{errors.email}</small>}</Field>
            <button className="button button-primary button-wide auth-primary" type="submit">Continue <ArrowRight size={16} /></button>
          </>}
          {register && registrationStep === 'password' && <>
            <Field label="Create password" hint="At least 12 characters. Use a password you do not use elsewhere."><span className="password-control"><input autoFocus type={visible.password ? 'text' : 'password'} autoComplete="new-password" minLength="12" maxLength="128" value={form.password} onChange={change('password')} aria-invalid={Boolean(errors.password)} /> <button type="button" onClick={() => setVisible((v) => ({ ...v, password: !v.password }))} aria-label={visible.password ? 'Hide password' : 'Show password'}>{visible.password ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>{errors.password && <small className="field-error">{errors.password}</small>}</Field>
            <Field label="Confirm password"><span className="password-control"><input type={visible.confirm ? 'text' : 'password'} autoComplete="new-password" maxLength="128" value={form.confirm_password} onChange={change('confirm_password')} aria-invalid={Boolean(errors.confirm_password)} /> <button type="button" onClick={() => setVisible((v) => ({ ...v, confirm: !v.confirm }))} aria-label={visible.confirm ? 'Hide confirmation' : 'Show confirmation'}>{visible.confirm ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>{errors.confirm_password && <small className="field-error">{errors.confirm_password}</small>}</Field>
            <div className="password-requirement"><ShieldCheck size={16} /><span>Use 12 or more characters and confirm that both entries match.</span></div>
            <div className="auth-button-row"><button type="button" className="button button-secondary" onClick={() => { setRegistrationStep('account'); setErrors({}); }}><ArrowLeft size={16} />Back</button><button className="button button-primary" type="submit" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17} /> : null}Create account <ArrowRight size={16} /></button></div>
          </>}
          {!register && <>
            <Field label="Email address"><input autoFocus type="email" autoComplete="email" value={form.email} onChange={change('email')} aria-invalid={Boolean(errors.email)} placeholder="you@example.com" />{errors.email && <small className="field-error">{errors.email}</small>}</Field>
            <Field label="Password"><span className="password-control"><input type={visible.password ? 'text' : 'password'} autoComplete="current-password" value={form.password} onChange={change('password')} aria-invalid={Boolean(errors.password)} /> <button type="button" onClick={() => setVisible((v) => ({ ...v, password: !v.password }))} aria-label={visible.password ? 'Hide password' : 'Show password'}>{visible.password ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>{errors.password && <small className="field-error">{errors.password}</small>}</Field>
            <button className="button button-primary button-wide auth-primary" type="submit" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17} /> : null}Sign in <ArrowRight size={16} /></button>
          </>}
        </form>
        <div className="auth-switch">{register ? 'Already have an account?' : 'New to IntelliVest?'} <button type="button" className="text-button" onClick={() => switchMode(register ? 'login' : 'register')}>{register ? 'Sign in' : 'Create an account'}</button></div>
      </div>
    </section>
    <footer className="auth-footer">IntelliVest provides financial analysis and recommendations. It does not execute trades.</footer>
  </main>;
}

function Field({ label, hint, children, className = '' }) {
  return <label className={`field ${className}`}><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>;
}

function Brand({ compact = false }) {
  return <div className={`brand ${compact ? 'brand-compact' : ''}`}><span className="brand-icon"><Activity size={19} strokeWidth={2.4} /></span><span>Intelli<span>Vest</span></span></div>;
}

function App() {
  const [authenticatedUser, setAuthenticatedUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  useEffect(() => {
    let mounted = true;
    api.currentUser().then(({ user }) => { if (mounted) setAuthenticatedUser(user); }).catch(() => {}).finally(() => { if (mounted) setAuthLoading(false); });
    const expired = () => setSessionExpired(true);
    window.addEventListener('intellivest:session-expired', expired);
    return () => { mounted = false; window.removeEventListener('intellivest:session-expired', expired); };
  }, []);
  async function signOut() {
    try { await api.logout(); } finally { setAuthenticatedUser(null); setSessionExpired(false); }
  }
  if (authLoading && !authenticatedUser) return <div className="app-loading"><Brand /><LoadingState label="Checking your session…" /></div>;
  if (!authenticatedUser) return <AuthPage onAuthenticated={(user) => { setAuthenticatedUser(user); setSessionExpired(false); }} />;
  return <>
    <InvestorWorkspace key={authenticatedUser.user_id} authenticatedUser={authenticatedUser} onLogout={signOut} />
    {sessionExpired && <div className="session-expired-overlay"><AuthPage onAuthenticated={(user) => { setAuthenticatedUser(user); setSessionExpired(false); }} /></div>}
  </>;
}

function nextOnboardingStep(income, summary, portfolios) {
  if (!income.length) return 'income';
  if (!summary?.has_evaluation) return 'expenses';
  if (!portfolios.length) return 'portfolio';
  return 'dashboard';
}

function InvestorWorkspace({ authenticatedUser, onLogout }) {
  const userId = authenticatedUser.user_id;
  const [profile, setProfile] = useState(authenticatedUser);
  const [summary, setSummary] = useState(null);
  const [income, setIncome] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [generation, setGeneration] = useState(null);
  const [portfolios, setPortfolios] = useState([]);
  const [portfolioId, setPortfolioId] = useState('');
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [risk, setRisk] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [page, setPage] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [mobileNav, setMobileNav] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(null);
  const [onboardingResolved, setOnboardingResolved] = useState(false);

  const currentPage = navItems.find((item) => item.id === page) || navItems[0];
  const selectedPortfolio = useMemo(() => portfolios.find((item) => item.portfolio_id === portfolioId) || null, [portfolios, portfolioId]);
  const unresolvedAlerts = alerts.filter((alert) => !alert.resolved_flag);

  const loadWorkspace = useCallback(async (idToLoad = userId) => {
    if (!idToLoad) return;
    setLoading(true);
    try {
      const [userResult, summaryResult, incomeResult, expenseResult, recommendationResult, portfolioResult, progressResult] = await Promise.all([
        api.getUser(idToLoad), api.getSummary(idToLoad), api.getIncome(idToLoad), api.getExpenses(idToLoad),
        api.getRecommendations(idToLoad), api.getPortfolios(idToLoad), api.getOnboardingProgress(idToLoad),
      ]);
      setProfile(userResult); setSummary(summaryResult); setIncome(incomeResult); setExpenses(expenseResult);
      setRecommendations(recommendationResult); setPortfolios(portfolioResult);
      setPortfolioId((previous) => portfolioResult.some((row) => row.portfolio_id === previous) ? previous : (portfolioResult[0]?.portfolio_id || ''));
      if (!onboardingResolved) {
        setOnboardingStep(progressResult?.step || nextOnboardingStep(incomeResult, summaryResult, portfolioResult));
        setOnboardingResolved(true);
      }
      setNotice(null);
    } catch (error) {
      setNotice({ type: 'error', message: errorMessage(error) });
      if (error instanceof ApiError && error.status === 401) window.dispatchEvent(new Event('intellivest:session-expired'));
    } finally { setLoading(false); }
  }, [userId, onboardingResolved]);

  useEffect(() => { if (userId) loadWorkspace(userId); }, [userId, loadWorkspace]);

  const loadPortfolio = useCallback(async (idToLoad = portfolioId, withRisk = false) => {
    if (!idToLoad) { setPortfolio(null); setHoldings([]); setRisk(null); return; }
    try {
      const [portfolioResult, holdingResult] = await Promise.all([api.getPortfolio(idToLoad), api.getHoldings(idToLoad)]);
      setPortfolio(portfolioResult); setHoldings(holdingResult);
      if (withRisk) setRisk(await api.getRisk(idToLoad));
    } catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); }
  }, [portfolioId]);

  const loadAlerts = useCallback(async (idToLoad = portfolioId) => {
    try { setAlerts(await api.getAlerts(idToLoad || undefined)); }
    catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); }
  }, [portfolioId]);

  useEffect(() => { if (!onboardingResolved || onboardingStep !== 'dashboard') return; if (portfolioId) loadPortfolio(portfolioId, page === 'risk' || page === 'overview'); else { setPortfolio(null); setHoldings([]); setRisk(null); } }, [page, portfolioId, loadPortfolio, onboardingResolved, onboardingStep]);
  useEffect(() => { if (onboardingResolved && onboardingStep === 'dashboard' && (page === 'alerts' || page === 'overview') && userId) loadAlerts(portfolioId); }, [page, portfolioId, userId, loadAlerts, onboardingResolved, onboardingStep]);

  async function perform(action, successMessage, refresh = loadWorkspace) {
    setBusy(true);
    try { const result = await action(); if (refresh) await refresh(); setNotice({ type: 'success', message: successMessage }); return result; }
    catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); return undefined; }
    finally { setBusy(false); }
  }

  if (loading && !onboardingResolved) return <div className="app-loading"><Brand /><LoadingState label="Loading your financial workspace…" /></div>;

  if (onboardingResolved && onboardingStep !== 'dashboard') return <GuidedOnboarding
    key={userId}
    user={profile || authenticatedUser}
    initialStep={onboardingStep}
    initialIncome={income}
    initialExpenses={expenses}
    initialSummary={summary}
    portfolios={portfolios}
    onLogout={onLogout}
    onDone={(data) => {
      setProfile(data.profile); setSummary(data.summary); setIncome(data.income); setExpenses(data.expenses);
      setPortfolios(data.portfolios); setPortfolioId(data.portfolioId); setPortfolio(data.portfolio);
      setHoldings(data.holdings); setRisk(data.risk); setAlerts(data.alerts); setRecommendations(data.recommendations);
      setGeneration(data.generation); setPage('overview'); setOnboardingStep('dashboard'); setNotice({ type: 'success', message: 'Your analysis is ready.' });
    }}
  />;

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
      <Brand />
      <div className="workspace-label">WORKSPACE</div>
      <nav className="primary-nav" aria-label="Main navigation">
        {navItems.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-link ${page === id ? 'active' : ''}`} onClick={() => { setPage(id); setMobileNav(false); }}>
          <Icon size={18} strokeWidth={1.9} /><span>{label}</span>{id === 'alerts' && unresolvedAlerts.length > 0 && <span className="nav-count">{unresolvedAlerts.length}</span>}
        </button>)}
      </nav>
      <div className="sidebar-bottom"><div className="local-status"><span className="status-dot" /><div><strong>Local workspace</strong><small>Data stays on this device</small></div></div><button className="profile-menu" onClick={onLogout}><span className="avatar">{profile?.full_name?.slice(0, 1)?.toUpperCase() || 'I'}</span><span className="profile-copy"><strong>{profile?.full_name || 'Investor'}</strong><small>{profile?.risk_tolerance_tier || 'Profile'}</small></span><LogOut size={16} /></button></div>
    </aside>
    {mobileNav && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobileNav(false)} />}
    <div className="main-column">
      <header className="topbar"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMobileNav(true)}><Menu size={20} /></button><div className="breadcrumb"><span>Workspace</span><span className="crumb-separator">/</span><strong>{currentPage.label}</strong></div><div className="topbar-actions"><span className="api-status"><span className="status-dot" />Connected to local API</span><button className="icon-button" aria-label="Refresh workspace" title="Refresh workspace" onClick={() => loadWorkspace()}><RefreshCw size={17} /></button></div></header>
      <main className="content-area"><Notice notice={notice} dismiss={() => setNotice(null)} />
        {loading && <LoadingState />}
        {!loading && page === 'overview' && <Overview profile={profile} summary={summary} portfolio={portfolio} holdings={holdings} risk={risk} alerts={unresolvedAlerts} recommendations={recommendations} go={setPage} />}
        {!loading && page === 'cashflow' && <CashflowPage userId={userId} profile={profile} summary={summary} income={income} expenses={expenses} busy={busy} perform={perform} onProfile={setProfile} onSummary={setSummary} onIncome={setIncome} onExpenses={setExpenses} />}
        {!loading && page === 'recommendations' && <RecommendationsPage userId={userId} summary={summary} recommendations={recommendations} generation={generation} setGeneration={setGeneration} busy={busy} setBusy={setBusy} setRecommendations={setRecommendations} setNotice={setNotice} />}
        {!loading && page === 'portfolios' && <PortfoliosPage userId={userId} portfolios={portfolios} setPortfolios={setPortfolios} portfolioId={portfolioId} setPortfolioId={setPortfolioId} portfolio={portfolio} holdings={holdings} busy={busy} setBusy={setBusy} setNotice={setNotice} refresh={loadWorkspace} refreshPortfolio={loadPortfolio} />}
        {!loading && page === 'risk' && <RiskPage portfolio={portfolio} holdings={holdings} risk={risk} portfolios={portfolios} portfolioId={portfolioId} setPortfolioId={setPortfolioId} loading={busy} refresh={() => loadPortfolio(portfolioId, true)} />}
        {!loading && page === 'alerts' && <AlertsPage alerts={alerts} portfolioId={portfolioId} portfolios={portfolios} setPortfolioId={setPortfolioId} refresh={loadAlerts} setNotice={setNotice} />}
        <footer className="page-footer"><span>IntelliVest · Local investor workspace</span><span>Market prices and risk metrics are supplied by the connected backend.</span></footer>
      </main>
    </div>
  </div>;
}

function Overview({ profile, summary, portfolio, holdings, risk, alerts, recommendations, go }) {
  const pending = recommendations.filter((item) => item.status_state === 'PENDING').length;
  const invested = portfolio?.portfolio_valuation;
  const recent = recommendations.slice(0, 4);
  return <>
    <PageHeading eyebrow="Your finances, in context" title={`Good to see you, ${profile?.full_name?.split(' ')[0] || 'investor'}`} description="A current view of your cash flow, portfolio, and risk." action={<button className="button button-secondary" onClick={() => go('cashflow')}><SlidersHorizontal size={16} />Update cash flow</button>} />
    <section className="metric-grid four-up workspace-top-metrics" aria-label="Financial overview">
      <MetricCard label="Investable surplus" value={money(summary?.investable_buffer)} helper="After your selected reserve" icon={Wallet} tone="green" />
      <MetricCard label="Portfolio value" value={money(portfolio?.portfolio_valuation)} helper={portfolio ? `${holdings.length} saved holding${holdings.length === 1 ? '' : 's'}` : 'No portfolio selected'} icon={BriefcaseBusiness} />
      <MetricCard label="Available cash" value={money(portfolio?.cash_balance)} helper="Cash recorded in portfolio" icon={ArrowUpRight} tone="violet" />
      <MetricCard label="Portfolio risk" value={risk ? money(risk.parametric_var_95) : holdings.length ? 'Loading' : 'Not available'} helper={risk ? 'VaR · 95% confidence' : holdings.length ? 'Risk data is being checked' : 'Add holdings to calculate'} icon={Gauge} tone="amber" />
    </section>
    <section className="dashboard-grid overview-grid">
      <article className="panel cash-summary-panel">
        <div className="panel-heading"><div><p className="eyebrow">Monthly cash flow</p><h2>What you can invest</h2></div><button className="text-button" onClick={() => go('cashflow')}>View cash flow <ArrowRight size={15} /></button></div>
        <div className="cash-flow-rows">
          <SummaryLine label="Monthly income" value={summary?.monthly_income} />
          <SummaryLine label="Mandatory expenses" value={summary?.monthly_mandatory_expenses} negative />
          <SummaryLine label="Optional expenses · shown separately" value={summary?.monthly_discretionary_expenses} />
          <SummaryLine label="Computed surplus" value={summary?.computed_surplus} strong />
          <SummaryLine label="Safety reserve" value={summary?.liquid_safety_reserve} />
        </div>
        <div className="buffer-band"><span>Available after reserve</span><strong>{money(summary?.investable_buffer)}</strong></div>
      </article>
      <article className="panel portfolio-snapshot">
        <div className="panel-heading"><div><p className="eyebrow">Portfolio snapshot</p><h2>{portfolio?.portfolio_name || 'No portfolio yet'}</h2></div><button className="icon-button" aria-label="Manage portfolios" onClick={() => go('portfolios')}><ArrowRight size={17} /></button></div>
        {portfolio ? <>
          <div className="snapshot-value">{money(portfolio.portfolio_valuation)}</div>
          <div className="snapshot-meta"><span>{holdings.length} holding{holdings.length === 1 ? '' : 's'}</span><span>Prices as of {dateLabel(portfolio.calculation_date)}</span></div>
          {holdings.length > 0 && <div className="mini-holdings">{holdings.slice(0, 3).map((holding) => <div className="mini-holding" key={holding.holding_id}><span className="ticker-chip">{holding.ticker_symbol}</span><span>{money(holding.market_value)}</span></div>)}</div>}
          <div className="overview-risk" aria-label="Portfolio risk indicators">
            <div><span>VaR · 95%</span><strong>{money(risk?.parametric_var_95)}</strong></div>
            <div><span>30-day volatility</span><strong>{percent(risk?.volatility_30d)}</strong></div>
            <div><span>Sector HHI</span><strong>{number(risk?.sector_hhi, 3)}</strong></div>
          </div>
          <button className="button button-secondary button-wide" onClick={() => go('risk')}>Review portfolio risk <ArrowRight size={15} /></button>
        </> : <EmptyState icon={BriefcaseBusiness} title="Start with a portfolio" copy="Create a portfolio to track holdings and view SQL-based risk analytics." action={<button className="button button-primary" onClick={() => go('portfolios')}>Create portfolio</button>} />}
      </article>
    </section>
    <section className="dashboard-grid lower-grid">
      <article className="panel">
        <div className="panel-heading"><div><p className="eyebrow">Investment ideas</p><h2>Recommendation status</h2></div><button className="text-button" onClick={() => go('recommendations')}>Open recommendations <ArrowRight size={15} /></button></div>
        {recent.length ? <div className="table-wrap"><table><thead><tr><th>Security</th><th>Amount</th><th>Shares</th><th>Status</th></tr></thead><tbody>{recent.map((item) => <tr key={item.rec_id}><td><strong>{item.stock_ticker}</strong></td><td>{money(item.recommended_amount)}</td><td>{number(item.shares, 0)}</td><td><StatusPill value={item.status_state} /></td></tr>)}</tbody></table></div> : <EmptyState icon={Sparkles} title="No recommendations yet" copy="Evaluate your cash flow to see affordable ideas based on current market quotes." action={<button className="button button-primary" onClick={() => go('recommendations')}>Explore recommendations</button>} />}
        <p className="panel-note">{pending ? `${pending} recommendation${pending === 1 ? '' : 's'} waiting for your decision.` : 'Accepting an idea records your intent. It does not place a brokerage order.'}</p>
      </article>
      <article className="panel alerts-preview">
        <div className="panel-heading"><div><p className="eyebrow">Risk monitoring</p><h2>Needs your attention</h2></div><button className="icon-button" aria-label="View all alerts" onClick={() => go('alerts')}><ArrowRight size={17} /></button></div>
        {alerts.length ? <div className="alert-list compact-alerts">{alerts.slice(0, 3).map((alert) => <AlertRow key={alert.alert_id} alert={alert} />)}</div> : <EmptyState icon={ShieldCheck} title="All clear for now" copy="A portfolio risk check will surface VaR, volatility, or sector concentration breaches here." />}
      </article>
    </section>
  </>;
}

function SummaryLine({ label, value, negative = false, strong = false }) {
  return <div className={`summary-line ${strong ? 'summary-strong' : ''}`}><span>{label}</span><span className={negative ? 'negative-value' : ''}>{negative && value != null ? '− ' : ''}{money(value)}</span></div>;
}

function StatusPill({ value }) {
  const normalized = String(value || 'UNKNOWN').toLowerCase();
  return <span className={`status-pill status-${normalized}`}>{String(value || 'Unknown').replaceAll('_', ' ')}</span>;
}

function CashflowPage({ userId, profile, summary, income, expenses, busy, perform, onProfile, onSummary, onIncome, onExpenses }) {
  const [reserve, setReserve] = useState(summary?.liquid_safety_reserve ?? '');
  const [incomeEditing, setIncomeEditing] = useState(null);
  const [expenseEditing, setExpenseEditing] = useState(null);
  const [showIncomeForm, setShowIncomeForm] = useState(false);
  const [showExpenseForm, setShowExpenseForm] = useState(false);
  const [tier, setTier] = useState(profile?.risk_tolerance_tier || 'MODERATE');
  useEffect(() => setReserve(summary?.liquid_safety_reserve ?? ''), [summary?.liquid_safety_reserve]);

  async function refreshCash() {
    const [summaryRow, incomeRows, expenseRows] = await Promise.all([api.getSummary(userId), api.getIncome(userId), api.getExpenses(userId)]);
    onSummary(summaryRow); onIncome(incomeRows); onExpenses(expenseRows);
  }
  async function submitIncome(body) {
    const result = incomeEditing ? await api.updateIncome(incomeEditing.income_id, body) : await api.addIncome(userId, body);
    setIncomeEditing(null); setShowIncomeForm(false); await api.evaluateCashflow(userId, reserve || '0'); await refreshCash(); return result;
  }
  async function submitExpense(body) {
    const result = expenseEditing ? await api.updateExpense(expenseEditing.expense_id, body) : await api.addExpense(userId, body);
    setExpenseEditing(null); setShowExpenseForm(false); await api.evaluateCashflow(userId, reserve || '0'); await refreshCash(); return result;
  }
  async function removeIncome(item) {
    await perform(async () => { await api.deleteIncome(item.income_id); await api.evaluateCashflow(userId, reserve || '0'); await refreshCash(); }, 'Income source removed.', null);
  }
  async function removeExpense(item) {
    await perform(async () => { await api.deleteExpense(item.expense_id); await api.evaluateCashflow(userId, reserve || '0'); await refreshCash(); }, 'Expense removed.', null);
  }
  async function evaluate() {
    await perform(async () => { const result = await api.evaluateCashflow(userId, reserve || '0'); onSummary(result); return result; }, 'Cash-flow evaluation saved.', null);
  }
  async function saveTier(event) {
    event.preventDefault();
    await perform(async () => { const updated = await api.updateRiskTolerance(userId, tier); onProfile(updated); return updated; }, 'Risk preference updated.', null);
  }
  const cashValues = summary || {};
  return <>
    <PageHeading eyebrow="Your monthly picture" title="Cash flow & profile" description="Add recurring income and expenses. IntelliVest normalizes yearly amounts to a monthly view, then calculates the buffer through the backend." action={<button className="button button-primary" onClick={evaluate} disabled={busy}><Check size={16} />Evaluate cash flow</button>} />
    <section className="metric-grid four-up compact-metrics">
      <MetricCard label="Monthly income" value={money(cashValues.monthly_income)} helper="Monthly equivalent" icon={ArrowUpRight} tone="green" />
      <MetricCard label="Mandatory expenses" value={money(cashValues.monthly_mandatory_expenses)} helper="Used to calculate surplus" icon={ArrowDownRight} tone="amber" />
      <MetricCard label="Computed surplus" value={money(cashValues.computed_surplus)} helper="Income less mandatory costs" icon={Activity} tone="blue" />
      <MetricCard label="Investable buffer" value={money(cashValues.investable_buffer)} helper="After your safety reserve" icon={Wallet} tone="violet" />
    </section>
    <section className="panel reserve-panel"><div><p className="eyebrow">Safety first</p><h2>Liquid safety reserve</h2><p className="muted">This amount is held back before the backend calculates your current investable buffer.</p></div><div className="reserve-control"><Field label="Reserve amount (INR)"><input aria-label="Liquid safety reserve" type="number" min="0" step="0.01" value={reserve} onChange={(event) => setReserve(event.target.value)} /></Field><button className="button button-secondary" onClick={evaluate} disabled={busy}>Save & recalculate</button></div></section>
    <section className="panel risk-preference-panel"><div><p className="eyebrow">Investor profile</p><h2>Risk preference</h2><p className="muted">This selection sets the starting allocation capacity used by the recommendation service.</p></div><form className="inline-form" onSubmit={saveTier}><select value={tier} onChange={(event) => setTier(event.target.value)}><option value="CONSERVATIVE">Conservative</option><option value="MODERATE">Moderate</option><option value="AGGRESSIVE">Aggressive</option></select><button className="button button-secondary" disabled={busy}>Save preference</button></form></section>
    <section className="content-section">
      <div className="section-heading"><div><p className="eyebrow">Earnings</p><h2>Income sources</h2></div><button className="button button-secondary" onClick={() => { setIncomeEditing(null); setShowIncomeForm(true); }}><CirclePlus size={16} />Add income</button></div>
      {showIncomeForm || incomeEditing ? <IncomeForm initial={incomeEditing} busy={busy} onCancel={() => { setIncomeEditing(null); setShowIncomeForm(false); }} onSubmit={(body) => perform(() => submitIncome(body), incomeEditing ? 'Income source updated.' : 'Income source added.', null)} /> : null}
      <div className="panel table-panel">{income.length ? <div className="table-wrap"><table><thead><tr><th>Source</th><th>Amount</th><th>Frequency</th><th /></tr></thead><tbody>{income.map((item) => <tr key={item.income_id}><td><strong>{item.source_category}</strong></td><td>{money(item.gross_amount)}</td><td>{item.frequency.toLowerCase()}</td><td className="row-actions"><button className="text-button" onClick={() => { setShowIncomeForm(false); setIncomeEditing(item); }}>Edit</button><button className="text-button danger-link" onClick={() => removeIncome(item)}>Remove</button></td></tr>)}</tbody></table></div> : <EmptyState icon={ArrowUpRight} title="No income sources added" copy="Add monthly or yearly income to start calculating your surplus." action={<button className="button button-secondary" onClick={() => setShowIncomeForm(true)}>Add income</button>} />}</div>
    </section>
    <section className="content-section">
      <div className="section-heading"><div><p className="eyebrow">Spending</p><h2>Expense items</h2></div><button className="button button-secondary" onClick={() => { setExpenseEditing(null); setShowExpenseForm(true); }}><CirclePlus size={16} />Add expense</button></div>
      {showExpenseForm || expenseEditing ? <ExpenseForm initial={expenseEditing} busy={busy} onCancel={() => { setExpenseEditing(null); setShowExpenseForm(false); }} onSubmit={(body) => perform(() => submitExpense(body), expenseEditing ? 'Expense updated.' : 'Expense added.', null)} /> : null}
      <div className="panel table-panel">{expenses.length ? <div className="table-wrap"><table><thead><tr><th>Expense</th><th>Amount</th><th>Frequency</th><th>Type</th><th /></tr></thead><tbody>{expenses.map((item) => <tr key={item.expense_id}><td><strong>{item.category}</strong></td><td>{money(item.amount)}</td><td>{item.recurrence_interval.toLowerCase()}</td><td><span className={`expense-tag ${item.is_mandatory ? 'mandatory' : ''}`}>{item.is_mandatory ? 'Mandatory' : 'Discretionary'}</span></td><td className="row-actions"><button className="text-button" onClick={() => { setShowExpenseForm(false); setExpenseEditing(item); }}>Edit</button><button className="text-button danger-link" onClick={() => removeExpense(item)}>Remove</button></td></tr>)}</tbody></table></div> : <EmptyState icon={ArrowDownRight} title="No expenses added" copy="Add mandatory and discretionary expenses for a more useful monthly view." action={<button className="button button-secondary" onClick={() => setShowExpenseForm(true)}>Add expense</button>} />}</div>
    </section>
  </>;
}

function IncomeForm({ initial, onSubmit, onCancel, busy }) {
  const [source, setSource] = useState(initial?.source_category || '');
  const [amount, setAmount] = useState(initial?.gross_amount || '');
  const [frequency, setFrequency] = useState(initial?.frequency || 'MONTHLY');
  return <form className="entry-form" onSubmit={(event) => { event.preventDefault(); onSubmit({ source_category: source, gross_amount: amount, frequency }); }}>
    <Field label="Source"><input required maxLength="100" value={source} onChange={(event) => setSource(event.target.value)} placeholder="Salary, freelance…" /></Field>
    <Field label="Amount (INR)"><input required type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} /></Field>
    <Field label="Frequency"><select value={frequency} onChange={(event) => setFrequency(event.target.value)}><option value="MONTHLY">Monthly</option><option value="YEARLY">Yearly</option></select></Field>
    <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}{initial ? 'Save changes' : 'Add source'}</button><button type="button" className="button button-plain" onClick={onCancel}>Cancel</button></div>
  </form>;
}

function ExpenseForm({ initial, onSubmit, onCancel, busy }) {
  const [category, setCategory] = useState(initial?.category || '');
  const [amount, setAmount] = useState(initial?.amount || '');
  const [frequency, setFrequency] = useState(initial?.recurrence_interval || 'MONTHLY');
  const [mandatory, setMandatory] = useState(initial?.is_mandatory ?? true);
  return <form className="entry-form expense-entry" onSubmit={(event) => { event.preventDefault(); onSubmit({ category, amount, recurrence_interval: frequency, is_mandatory: mandatory }); }}>
    <Field label="Expense"><input required maxLength="100" value={category} onChange={(event) => setCategory(event.target.value)} placeholder="Rent, utilities…" /></Field>
    <Field label="Amount (INR)"><input required type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} /></Field>
    <Field label="Frequency"><select value={frequency} onChange={(event) => setFrequency(event.target.value)}><option value="MONTHLY">Monthly</option><option value="YEARLY">Yearly</option></select></Field>
    <Field label="Classification"><select value={mandatory ? 'mandatory' : 'discretionary'} onChange={(event) => setMandatory(event.target.value === 'mandatory')}><option value="mandatory">Mandatory</option><option value="discretionary">Discretionary</option></select></Field>
    <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}{initial ? 'Save changes' : 'Add expense'}</button><button type="button" className="button button-plain" onClick={onCancel}>Cancel</button></div>
  </form>;
}

function RecommendationsPage({ userId, summary, recommendations, generation, setGeneration, busy, setBusy, setRecommendations, setNotice }) {
  const [filter, setFilter] = useState('ALL');
  const [generating, setGenerating] = useState(false);
  async function generate() {
    setGenerating(true); setNotice(null);
    try {
      const result = await api.generateRecommendations(userId);
      setGeneration(result);
      setRecommendations(await api.getRecommendations(userId));
      setNotice({ type: 'success', message: result.recommendations?.length ? 'Recommendations refreshed using current market quotes and risk policy.' : (result.reason || 'No recommendations fit the current policy and budget.') });
    } catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); }
    finally { setGenerating(false); }
  }
  async function decide(item, decision) {
    setBusy(true);
    try {
      await api.decideRecommendation(userId, item.rec_id, decision);
      setRecommendations(await api.getRecommendations(userId));
      setNotice({ type: 'success', message: decision === 'ACCEPTED' ? 'Intent recorded. No brokerage order was sent.' : 'Recommendation declined.' });
    } catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); }
    finally { setBusy(false); }
  }
  const visible = recommendations.filter((item) => filter === 'ALL' || item.status_state === filter);
  const activePolicy = generation;
  return <>
    <PageHeading eyebrow="Affordable ideas" title="Recommendations" description="Whole-share suggestions use current database quotes, your evaluated investable buffer, and active portfolio risk restrictions." action={<button className="button button-primary" onClick={generate} disabled={generating || busy || Number(summary?.investable_buffer || 0) <= 0}>{generating ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />}Generate recommendations</button>} />
    <section className="recommendation-banner"><div className="banner-icon"><Wallet size={20} /></div><div><span>Available to invest now</span><strong>{money(summary?.investable_buffer)}</strong></div><p>Recommendations use a portion of this buffer. A pending batch must be resolved before another is generated.</p><button className="text-button" onClick={generate} disabled={generating || busy}>Refresh ideas <ArrowRight size={15} /></button></section>
    {activePolicy && <section className="policy-panel"><div className="policy-icon"><ShieldCheck size={18} /></div><div><strong>{activePolicy.reason || 'Current recommendation policy'}</strong><p>Capacity multiplier {number(activePolicy.policy_multiplier, 2)} · allocation budget {money(activePolicy.allocation_budget)}{activePolicy.blocked_sectors?.length ? ` · restricted sectors: ${activePolicy.blocked_sectors.join(', ')}` : ''}</p></div></section>}
    <section className="section-heading list-heading"><div><p className="eyebrow">Your list</p><h2>Saved recommendations</h2></div><Field label="Status"><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="ALL">All statuses</option><option value="PENDING">Pending</option><option value="ACCEPTED">Accepted</option><option value="REJECTED">Rejected</option></select></Field></section>
    <section className="panel table-panel">
      {visible.length ? <div className="table-wrap"><table><thead><tr><th>Security</th><th>Recommendation</th><th>Target allocation</th><th>Shares</th><th>Status</th><th>Risk context</th><th>Decision</th></tr></thead><tbody>{visible.map((item) => <tr key={item.rec_id}><td><div className="security-name"><strong>{item.stock_ticker}</strong><small>Market quote backed</small></div></td><td>{money(item.recommended_amount)}</td><td>{number(item.target_allocation_pct)}%</td><td>{number(item.shares, 0)}</td><td><StatusPill value={item.status_state} /></td><td className="explanation-cell">{item.explanation || 'Current policy applied.'}</td><td>{item.status_state === 'PENDING' ? <div className="decision-actions"><button className="button button-small button-accept" disabled={busy} onClick={() => decide(item, 'ACCEPTED')}>Accept</button><button className="button button-small button-reject" disabled={busy} onClick={() => decide(item, 'REJECTED')}>Decline</button></div> : <span className="muted small-copy">Recorded</span>}</td></tr>)}</tbody></table></div> : <EmptyState icon={Sparkles} title={filter === 'ALL' ? 'No recommendations to show' : `No ${filter.toLowerCase()} recommendations`} copy={Number(summary?.investable_buffer || 0) > 0 ? 'Generate a batch to get whole-share ideas sized to your current buffer.' : 'Evaluate your cash flow and reserve first. The service will return no ideas when the buffer is zero.'} action={<button className="button button-primary" onClick={generate} disabled={generating || Number(summary?.investable_buffer || 0) <= 0}>Generate recommendations</button>} />}
    </section>
    <p className="disclaimer-line"><CircleHelp size={15} /> Acceptance records your intent only. No brokerage order is executed. Recommendations are deterministic MVP suggestions, not return predictions.</p>
  </>;
}

function PortfoliosPage({ userId, portfolios, setPortfolios, portfolioId, setPortfolioId, portfolio, holdings, busy, setBusy, setNotice, refresh, refreshPortfolio }) {
  const [showCreate, setShowCreate] = useState(false);
  const [showHolding, setShowHolding] = useState(false);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [cash, setCash] = useState('0');
  const [limit, setLimit] = useState('0.250');
  const [editName, setEditName] = useState('');
  const [editLimit, setEditLimit] = useState('');
  const [search, setSearch] = useState('');
  const [securities, setSecurities] = useState([]);
  const [securityId, setSecurityId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [averagePrice, setAveragePrice] = useState('');
  const [editingHolding, setEditingHolding] = useState(null);
  useEffect(() => { if (portfolio) { setEditName(portfolio.portfolio_name); setEditLimit(String(portfolio.target_hhi_limit)); } }, [portfolio?.portfolio_id, portfolio?.portfolio_name, portfolio?.target_hhi_limit]);
  useEffect(() => { let mounted = true; api.getSecurities(search).then((rows) => { if (mounted) { setSecurities(rows); if (!securityId && rows[0]) setSecurityId(rows[0].security_id); } }).catch(() => {}); return () => { mounted = false; }; }, [search]);

  async function action(run, message, refreshMode = 'all') {
    setBusy(true);
    try { const result = await run(); if (refreshMode === 'all') await refresh(); else await refreshPortfolio(); setNotice({ type: 'success', message }); return result; }
    catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); return undefined; }
    finally { setBusy(false); }
  }
  async function create(event) {
    event.preventDefault();
    const result = await action(() => api.createPortfolio({ user_id: userId, portfolio_name: name, cash_balance: cash, target_hhi_limit: limit }), 'Portfolio created.');
    if (result) { setShowCreate(false); setName(''); setPortfolioId(result.portfolio_id); }
  }
  async function savePortfolio(event) {
    event.preventDefault();
    const result = await action(() => api.updatePortfolio(portfolioId, { portfolio_name: editName, target_hhi_limit: editLimit }), 'Portfolio details updated.', 'portfolio');
    if (result) setEditing(false);
  }
  async function removePortfolio() {
    if (!window.confirm('Delete this portfolio? The API will reject deletion if it has trade, alert, or feedback history.')) return;
    const result = await action(() => api.deletePortfolio(portfolioId), 'Portfolio deleted.');
    if (result === null) {
      const remaining = await api.getPortfolios(userId);
      setPortfolios(remaining);
      setPortfolioId(remaining[0]?.portfolio_id || '');
    }
  }
  async function addHolding(event) {
    event.preventDefault();
    const security = securities.find((row) => row.security_id === securityId);
    if (!security) return;
    const result = await action(() => api.addHolding(portfolioId, { security_id: securityId, quantity: Number(quantity), average_buy_price: averagePrice || security.latest_price }), 'Imported holding added.', 'portfolio');
    if (result) { setShowHolding(false); setQuantity('1'); setAveragePrice(''); }
  }
  async function saveHolding(event) {
    event.preventDefault();
    const result = await action(() => api.updateHolding(portfolioId, editingHolding.security_id, { security_id: editingHolding.security_id, quantity: Number(editingHolding.quantity), average_buy_price: editingHolding.average_buy_price }), 'Imported holding updated.', 'portfolio');
    if (result) setEditingHolding(null);
  }
  async function removeHolding(row) {
    const result = await action(() => api.removeHolding(portfolioId, row.security_id), 'Imported holding removed.', 'portfolio');
    return result;
  }
  return <>
    <PageHeading eyebrow="Your investments" title="Portfolios & holdings" description="Track a portfolio with current backend valuations. Imported holdings can be edited only before simulated trade history exists." action={<button className="button button-primary" onClick={() => setShowCreate((value) => !value)}><CirclePlus size={16} />New portfolio</button>} />
    {showCreate && <form className="entry-form portfolio-create" onSubmit={create}><Field label="Portfolio name"><input required maxLength="255" value={name} onChange={(event) => setName(event.target.value)} placeholder="Long-term portfolio" /></Field><Field label="Opening cash (INR)"><input required type="number" min="0" step="0.01" value={cash} onChange={(event) => setCash(event.target.value)} /></Field><Field label="Target HHI limit"><input required type="number" min="0.001" max="1" step="0.001" value={limit} onChange={(event) => setLimit(event.target.value)} /></Field><button className="button button-primary" disabled={busy}>Create</button><button type="button" className="button button-plain" onClick={() => setShowCreate(false)}>Cancel</button></form>}
    {!portfolios.length ? <section className="panel"><EmptyState icon={BriefcaseBusiness} title="No portfolios yet" copy="Create a portfolio to track cash, imported holdings, and backend-computed risk." action={<button className="button button-primary" onClick={() => setShowCreate(true)}>Create portfolio</button>} /></section> : <>
      <div className="portfolio-toolbar"><Field label="Selected portfolio"><select value={portfolioId} onChange={(event) => setPortfolioId(event.target.value)}>{portfolios.map((row) => <option value={row.portfolio_id} key={row.portfolio_id}>{row.portfolio_name}</option>)}</select></Field>{portfolio && <div className="toolbar-value"><span>Current value</span><strong>{money(portfolio.portfolio_valuation)}</strong></div>}</div>
      {portfolio && <section className="metric-grid three-up compact-metrics"><MetricCard label="Portfolio valuation" value={money(portfolio.portfolio_valuation)} helper={`Market data as of ${dateLabel(portfolio.calculation_date)}`} icon={BriefcaseBusiness} tone="blue" /><MetricCard label="Cash balance" value={money(portfolio.cash_balance)} helper="Available in this simulated portfolio" icon={Wallet} tone="green" /><MetricCard label="Holdings" value={number(holdings.length, 0)} helper="Imported or simulated positions" icon={Activity} tone="violet" /></section>}
      <section className="panel portfolio-details"><div className="panel-heading"><div><p className="eyebrow">Portfolio settings</p><h2>{portfolio?.portfolio_name}</h2></div><div className="panel-actions"><button className="button button-secondary" onClick={() => setEditing((value) => !value)}><SlidersHorizontal size={15} />Edit details</button><button className="button button-plain danger-link" onClick={removePortfolio}>Delete</button></div></div>
        {editing && <form className="entry-form edit-portfolio-form" onSubmit={savePortfolio}><Field label="Portfolio name"><input required maxLength="255" value={editName} onChange={(event) => setEditName(event.target.value)} /></Field><Field label="Target HHI limit"><input required type="number" min="0.001" max="1" step="0.001" value={editLimit} onChange={(event) => setEditLimit(event.target.value)} /></Field><div className="form-actions"><button className="button button-primary" disabled={busy}>Save</button><button type="button" className="button button-plain" onClick={() => setEditing(false)}>Cancel</button></div></form>}
      </section>
      <section className="section-heading"><div><p className="eyebrow">Positions</p><h2>Holdings</h2></div><button className="button button-secondary" onClick={() => setShowHolding((value) => !value)}><CirclePlus size={16} />Import holding</button></section>
      {showHolding && <form className="entry-form holding-form" onSubmit={addHolding}><Field label="Security"><select value={securityId} onChange={(event) => setSecurityId(event.target.value)}>{securities.map((item) => <option key={item.security_id} value={item.security_id}>{item.ticker_symbol} · {item.sector_name} · {money(item.latest_price)}</option>)}</select></Field><Field label="Quantity"><input required type="number" min="1" step="1" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></Field><Field label="Average purchase price (INR)" hint="Defaults to the latest quote if left blank."><input type="number" min="0.01" step="0.01" value={averagePrice} onChange={(event) => setAveragePrice(event.target.value)} /></Field><div className="form-actions"><button className="button button-primary" disabled={busy || !securityId}>Add imported position</button><button type="button" className="button button-plain" onClick={() => setShowHolding(false)}>Cancel</button></div><p className="form-hint-wide">Imported position edits are locked after the first simulated trade to keep ledger and cash history consistent.</p></form>}
      <section className="panel table-panel">{holdings.length ? <div className="table-wrap"><table><thead><tr><th>Security</th><th>Sector</th><th>Shares</th><th>Average cost</th><th>Latest quote</th><th>Market value</th><th>Price date</th><th /></tr></thead><tbody>{holdings.map((row) => <tr key={row.holding_id}><td><div className="security-name"><strong>{row.ticker_symbol}</strong><small>{row.company_name}</small></div></td><td>{row.sector_name}</td><td>{number(row.quantity, 0)}</td><td>{money(row.average_buy_price)}</td><td>{money(row.latest_price)}</td><td><strong>{money(row.market_value)}</strong></td><td>{dateLabel(row.price_date)}</td><td className="row-actions"><button className="text-button" onClick={() => setEditingHolding({ ...row })}>Edit</button><button className="text-button danger-link" onClick={() => removeHolding(row)}>Remove</button></td></tr>)}</tbody></table></div> : <EmptyState icon={Activity} title="No holdings in this portfolio" copy="Import a real security position. Current prices come from the risk database." action={<button className="button button-secondary" onClick={() => setShowHolding(true)}>Import holding</button>} />}</section>
      {editingHolding && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setEditingHolding(null); }}><form className="modal-card" onSubmit={saveHolding}><button type="button" className="modal-close icon-button" onClick={() => setEditingHolding(null)} aria-label="Close"><X size={17} /></button><p className="eyebrow">Imported position</p><h2>Edit {editingHolding.ticker_symbol}</h2><Field label="Quantity"><input required type="number" min="1" step="1" value={editingHolding.quantity} onChange={(event) => setEditingHolding((item) => ({ ...item, quantity: event.target.value }))} /></Field><Field label="Average purchase price (INR)"><input required type="number" min="0.01" step="0.01" value={editingHolding.average_buy_price} onChange={(event) => setEditingHolding((item) => ({ ...item, average_buy_price: event.target.value }))} /></Field><button className="button button-primary button-wide" disabled={busy}>Save holding</button></form></div>}
    </>}
  </>;
}

function RiskPage({ portfolio, holdings, risk, portfolios, portfolioId, setPortfolioId, loading, refresh }) {
  return <>
    <PageHeading eyebrow="Portfolio health" title="Risk analytics" description="Metrics are evaluated by PostgreSQL using the portfolio’s underlying quote history and current holdings." action={<div className="risk-toolbar"><Field label="Portfolio"><select value={portfolioId} onChange={(event) => setPortfolioId(event.target.value)}>{portfolios.map((row) => <option key={row.portfolio_id} value={row.portfolio_id}>{row.portfolio_name}</option>)}</select></Field><button className="button button-secondary" onClick={refresh} disabled={!portfolioId || loading}><RefreshCw size={15} />Refresh risk check</button></div>} />
    {!portfolioId ? <section className="panel"><EmptyState icon={Gauge} title="Select a portfolio first" copy="Create a portfolio and add holdings to evaluate its risk." /></section> : !risk ? <section className="panel"><LoadingState label="Waiting for PostgreSQL risk analytics…" /></section> : <>
      <div className="risk-data-line"><span><span className={`risk-status-dot ${risk.calculation_status === 'ok' ? 'good' : 'warn'}`} />{risk.calculation_status?.replaceAll('_', ' ')}</span><span>Data date: {dateLabel(risk.calculation_date)}</span><span>Return observations: {number(risk.historical_observations, 0)} / 252</span><span>Portfolio value: {money(risk.portfolio_valuation)}</span></div>
      <section className="metric-grid three-up risk-metrics">
        <RiskMetric label="Value at Risk · 95%" value={money(risk.parametric_var_95)} helper="Estimated one-day loss threshold from portfolio volatility." badge="Parametric" tone="amber" />
        <RiskMetric label="Historical VaR · 95%" value={money(risk.historical_var_95)} helper="5th percentile portfolio loss across the available 252-return window." badge="Historical" tone="blue" />
        <RiskMetric label="Conditional Value at Risk (CVaR)" value={money(risk.cvar_95)} helper={`CVaR estimates the average loss in the worst market outcomes beyond the VaR threshold. ${number((risk.cvar_confidence_level || 0.95) * 100, 0)}% confidence · ${number(risk.cvar_horizon_trading_days, 1)}-day horizon · ${number(risk.cvar_observations, 0)} / ${number(risk.cvar_window, 0)} observations · data through ${dateLabel(risk.cvar_data_timestamp)}.`} badge={`Historical · ${number((risk.cvar_confidence_level || 0.95) * 100, 0)}%`} tone="amber" />
        <RiskMetric label="Sharpe ratio" value={number(risk.sharpe_ratio, 3)} helper="Annualized return above the risk-free rate per unit of volatility." badge="Annualized" tone="green" />
        <RiskMetric label="30-observation volatility" value={percent(risk.volatility_30d)} helper="Standard deviation of daily portfolio returns over the latest 30 observations." badge="Daily returns" tone="violet" />
        <RiskMetric label="Sector concentration · HHI" value={number(risk.sector_hhi, 3)} helper={`Target limit: ${number(risk.target_hhi_limit, 3)}. Higher values indicate concentration.`} badge="Portfolio mix" tone={risk.sector_hhi > risk.target_hhi_limit ? 'red' : 'green'} />
      </section>
      {risk.calculation_status !== 'ok' && <div className="notice notice-info"><CircleHelp size={17} /><span>This portfolio does not yet have a complete history for every metric. Missing values remain blank until PostgreSQL has sufficient real observations.</span></div>}
      {risk.feedback_delivery && <section className="policy-panel feedback-panel"><span className="policy-icon"><ShieldCheck size={18} /></span><div><strong>Risk feedback status</strong><p>{risk.feedback_delivery.events_applied} event(s) applied · {risk.feedback_delivery.pending_events} pending · {risk.new_alerts?.length || 0} new alert(s) from this check. New recommendation requests use the updated policy.</p></div></section>}
      {portfolio && holdings.length > 0 && <Suspense fallback={<section className="panel"><LoadingState label="Loading portfolio chart…" /></section>}><HoldingsChart holdings={holdings} /></Suspense>}
    </>}
  </>;
}

function RiskMetric({ label, value, helper, badge, tone }) {
  return <article className={`risk-card risk-${tone}`}><div className="risk-card-top"><span className="eyebrow">{label}</span><span className="metric-badge">{badge}</span></div><strong>{value}</strong><p>{helper}</p></article>;
}

function AlertsPage({ alerts, portfolioId, portfolios, setPortfolioId, refresh, setNotice }) {
  const [filter, setFilter] = useState('OPEN');
  const visible = alerts.filter((alert) => filter === 'ALL' || (filter === 'OPEN' ? !alert.resolved_flag : alert.resolved_flag));
  async function resolve(alert) {
    try { await api.resolveAlert(alert.alert_id); await refresh(portfolioId); setNotice({ type: 'success', message: 'Alert marked as resolved. The feedback policy has been refreshed.' }); }
    catch (error) { setNotice({ type: 'error', message: errorMessage(error) }); }
  }
  return <>
    <PageHeading eyebrow="Risk events" title="Alerts" description="Threshold breaches are recorded by the risk service and can change the policy used by later recommendations." action={<div className="risk-toolbar"><Field label="Portfolio"><select value={portfolioId} onChange={(event) => setPortfolioId(event.target.value)}><option value="">All portfolios</option>{portfolios.map((row) => <option key={row.portfolio_id} value={row.portfolio_id}>{row.portfolio_name}</option>)}</select></Field><button className="button button-secondary" onClick={() => refresh(portfolioId)}><RefreshCw size={15} />Refresh</button></div>} />
    <div className="alert-summary-row"><div className="alert-count-card"><span className="alert-count-number">{number(alerts.filter((item) => !item.resolved_flag).length, 0)}</span><span>Unresolved for selected portfolio</span></div><div className="alert-explainer"><ShieldCheck size={19} /><p>VaR and volatility breaches reduce future allocation capacity. HHI breaches restrict new recommendations in the most concentrated sector. Resolving a cleared alert refreshes the policy.</p></div></div>
    <section className="section-heading list-heading"><div><p className="eyebrow">Risk history</p><h2>Portfolio alerts</h2></div><Field label="Show"><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="OPEN">Unresolved</option><option value="ALL">All alerts</option><option value="RESOLVED">Resolved</option></select></Field></section>
    {visible.length ? <section className="alert-list alert-page-list">{visible.map((alert) => <article className={`alert-card ${alert.resolved_flag ? 'alert-resolved' : ''}`} key={alert.alert_id}><span className={`alert-symbol ${alert.resolved_flag ? 'resolved' : alert.breached_metric.includes('VAR') ? 'red' : 'amber'}`}>{alert.resolved_flag ? <Check size={17} /> : <Bell size={17} />}</span><div className="alert-content"><div className="alert-title-row"><h3>{alertLabel(alert.breached_metric)}</h3><StatusPill value={alert.resolved_flag ? 'RESOLVED' : 'OPEN'} /></div><p>{alertDescription(alert.breached_metric)}</p><div className="alert-meta"><span>{portfolios.find((item) => item.portfolio_id === alert.portfolio_id)?.portfolio_name || 'Portfolio'}</span><span>{number(alert.drift_magnitude_pct)}% beyond configured threshold</span><span>{dateLabel(alert.created_at)}</span></div></div>{!alert.resolved_flag && <button className="button button-secondary button-small" onClick={() => resolve(alert)}>Mark resolved</button>}</article>)}</section> : <section className="panel"><EmptyState icon={Bell} title={filter === 'OPEN' ? 'No unresolved alerts' : 'No alerts to show'} copy="Risk checks can create alerts for VaR, volatility, or sector concentration thresholds." /></section>}
  </>;
}

function AlertRow({ alert }) {
  return <div className="alert-row"><span className={`alert-dot ${alert.breached_metric.includes('VAR') ? 'red' : 'amber'}`} /><div><strong>{alertLabel(alert.breached_metric)}</strong><small>{dateLabel(alert.created_at)} · {number(alert.drift_magnitude_pct)}% over limit</small></div></div>;
}
function alertLabel(metric) {
  return ({ VAR_95_BREACH: 'VaR threshold breached', VOLATILITY_SPIKE: 'Volatility threshold breached', SECTOR_HHI_EXCEEDED: 'Sector concentration exceeded' })[metric] || String(metric || 'Risk alert').replaceAll('_', ' ');
}
function alertDescription(metric) {
  return ({ VAR_95_BREACH: 'Portfolio parametric VaR exceeded the configured percentage of portfolio value.', VOLATILITY_SPIKE: 'Recent daily portfolio volatility exceeded the configured risk limit.', SECTOR_HHI_EXCEEDED: 'The portfolio sector concentration exceeded its target HHI limit.' })[metric] || 'The risk service recorded a portfolio threshold breach.';
}

export default App;
