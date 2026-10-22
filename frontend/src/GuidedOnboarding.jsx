import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowLeft, ArrowRight, Check, CirclePlus, LoaderCircle, Search, ShieldCheck, Trash2 } from 'lucide-react';
import { api, ApiError } from './api.js';

const steps = [
  ['account', 'Account details'], ['password', 'Password'], ['income', 'Income'], ['expenses', 'Expenses'],
  ['safety', 'Safety & risk'], ['evaluation', 'Financial evaluation'], ['portfolio', 'Portfolio'], ['analysis', 'Analysis'],
];
const incomeSources = ['Salary', 'Business', 'Freelance', 'Investment income', 'Other'];
const expenseCategories = ['Housing or rent', 'Groceries and food', 'Electricity and utilities', 'Transportation', 'Education', 'Loan or EMI payments', 'Insurance', 'Healthcare', 'Subscriptions and entertainment', 'Other expenses'];
const money = (value) => value === null || value === undefined || value === '' ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(value));
const errorMessage = (error) => error instanceof ApiError ? error.message : (error?.message || 'Something went wrong. Please try again.');

export default function GuidedOnboarding({ authenticationError, user, initialStep, initialIncome, initialExpenses, initialSummary, portfolios, onDone, onLogout }) {
  const [step, setStep] = useState(initialStep);
  const [incomes, setIncomes] = useState(() => initialIncome.length
    ? initialIncome.map((row) => ({ ...row, localId: row.income_id || crypto.randomUUID() }))
    : [{ localId: crypto.randomUUID(), source_category: 'Salary', gross_amount: '', frequency: 'MONTHLY' }]);
  const [expenses, setExpenses] = useState(() => initialExpenses.map((row) => ({ ...row, localId: row.expense_id || crypto.randomUUID() })));
  const [summary, setSummary] = useState(initialSummary);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(portfolios[0]?.portfolio_id || '');
  const [createdPortfolio, setCreatedPortfolio] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const stepIndex = steps.findIndex(([id]) => id === step);
  const meta = useMemo(() => ({
    income: ['Let’s understand your income.', 'Add the sources that support your monthly finances. We’ll normalize yearly income using IntelliVest’s existing calculation.'],
    expenses: ['Where does your money go?', 'Record recurring costs. Mark each one as necessary or optional so your financial picture stays clear.'],
    safety: ['Let’s understand your financial safety.', 'Choose the cash reserve to keep aside and the investment risk level that feels right to you.'],
    evaluation: ['Your Financial Overview', 'Here is your real cash-flow evaluation from IntelliVest. You can go back and edit any of these answers.'],
    portfolio: ['Do you already own stocks?', 'Add your current investments so IntelliVest can assess your portfolio before preparing recommendations.'],
    analysis: ['Your analysis is underway.', 'IntelliVest is using your saved financial profile, portfolio data, market quotes, and current risk policy.'],
  }), []);

  async function transact(operation, nextStep) {
    setBusy(true); setError('');
    try { const result = await operation(); if (nextStep) { await api.updateOnboardingProgress(user.user_id, nextStep); setStep(nextStep); } return result; }
    catch (issue) { setError(errorMessage(issue)); return undefined; }
    finally { setBusy(false); }
  }

  async function goTo(nextStep) {
    setBusy(true); setError('');
    try { await api.updateOnboardingProgress(user.user_id, nextStep); setStep(nextStep); }
    catch (issue) { setError(errorMessage(issue)); }
    finally { setBusy(false); }
  }

  async function saveIncome(rows) {
    const saved = [];
    for (const row of rows) {
      const body = { source_category: row.source_category, gross_amount: row.gross_amount, frequency: row.frequency };
      const result = row.income_id ? await api.updateIncome(row.income_id, body) : await api.addIncome(user.user_id, body);
      saved.push(result);
      setIncomes((current) => current.map((item) => item.localId === row.localId ? { ...result, localId: row.localId } : item));
    }
    return saved;
  }

  async function saveExpenses(rows) {
    const saved = [];
    for (const row of rows) {
      const body = { category: row.category, amount: row.amount, is_mandatory: row.is_mandatory, recurrence_interval: row.recurrence_interval };
      const result = row.expense_id ? await api.updateExpense(row.expense_id, body) : await api.addExpense(user.user_id, body);
      saved.push(result);
      setExpenses((current) => current.map((item) => item.localId === row.localId ? { ...result, localId: row.localId } : item));
    }
    return saved;
  }

  if (step === 'analysis') return <AnalysisStep userId={user.user_id} preferredPortfolioId={selectedPortfolioId} summary={summary} onBack={() => goTo('portfolio')} onDone={async (data) => { await api.updateOnboardingProgress(user.user_id, 'dashboard'); onDone(data); }} />;
  const [title, description] = meta[step] || meta.income;
  return <main className="wizard-shell">
    <header className="wizard-top"><Brand /><button className="wizard-account" type="button" onClick={onLogout}><span className="wizard-avatar">{user.full_name?.slice(0, 1)?.toUpperCase() || 'I'}</span><span>{user.full_name || 'Your account'}</span><span className="wizard-signout">Sign out</span></button></header>
    <section className="wizard-progress" aria-label="Onboarding progress">
      <div className="wizard-progress-copy"><span>Investor setup</span><strong>Step {stepIndex + 1} of {steps.length} · {steps[stepIndex]?.[1]}</strong></div>
      <div className="wizard-progress-track">{steps.map(([id, label], index) => <span key={id} className={index <= stepIndex ? 'done' : ''} title={label} />)}</div>
    </section>
    <section className="wizard-content" key={step}>
      <div className="wizard-heading"><span className="wizard-heading-mark"><Activity size={21} /></span><p className="eyebrow">Your financial workspace</p><h1>{title}</h1><p>{description}</p></div>
      {(error || authenticationError) && <div className="wizard-error" role="alert">{error || authenticationError}</div>}
      {step === 'income' && <IncomeStep rows={incomes} setRows={setIncomes} busy={busy} onBack={onLogout} onContinue={(rows) => transact(async () => { await saveIncome(rows); return true; }, 'expenses')} />}
      {step === 'expenses' && <ExpenseStep rows={expenses} setRows={setExpenses} busy={busy} onBack={() => goTo('income')} onContinue={(rows) => transact(async () => { await saveExpenses(rows); return true; }, 'safety')} />}
      {step === 'safety' && <SafetyStep user={user} summary={summary} busy={busy} onBack={() => goTo('expenses')} onContinue={(reserve, tier) => transact(async () => {
        await api.updateRiskTolerance(user.user_id, tier);
        const result = await api.evaluateCashflow(user.user_id, reserve);
        setSummary(result);
        return result;
      }, 'evaluation')} />}
      {step === 'evaluation' && <EvaluationStep summary={summary} busy={busy} onBack={() => goTo('safety')} onEditIncome={() => goTo('income')} onEditExpenses={() => goTo('expenses')} onContinue={() => goTo('portfolio')} />}
      {step === 'portfolio' && <PortfolioStep user={user} savedPortfolios={createdPortfolio && !portfolios.some((item) => item.portfolio_id === createdPortfolio.portfolio_id) ? [...portfolios, createdPortfolio] : portfolios} busy={busy} createdPortfolio={createdPortfolio} onCreated={setCreatedPortfolio} onBack={() => goTo('evaluation')} onContinue={(portfolioId) => { setSelectedPortfolioId(portfolioId); goTo('analysis'); }} onError={setError} />}
    </section>
    <footer className="wizard-footer"><ShieldCheck size={15} /><span>Your data is saved to your secure IntelliVest account as you continue.</span></footer>
  </main>;
}

function Brand() { return <div className="brand"><span className="brand-icon"><Activity size={19} strokeWidth={2.4} /></span><span>Intelli<span>Vest</span></span></div>; }
function Field({ label, hint, error, children }) { return <label className={`wizard-field ${error ? 'has-error' : ''}`}><span>{label}</span>{children}{hint && <small>{hint}</small>}{error && <small className="field-error">{error}</small>}</label>; }
function StepActions({ onBack, onContinue, backLabel = 'Back', continueLabel = 'Continue', busy = false, disabled = false }) {
  return <div className="wizard-actions"><button className="button button-secondary" type="button" onClick={onBack} disabled={busy}><ArrowLeft size={16} />{backLabel}</button><button className="button button-primary" type={onContinue ? 'button' : 'submit'} onClick={onContinue} disabled={busy || disabled}>{busy ? <LoaderCircle className="spin" size={17} /> : null}{continueLabel}<ArrowRight size={16} /></button></div>;
}

function IncomeStep({ rows, setRows, busy, onBack, onContinue }) {
  const [errors, setErrors] = useState({});
  function update(index, key, value) { setRows((current) => current.map((row, i) => i === index ? { ...row, [key]: value } : row)); }
  function add() { setRows((current) => [...current, { localId: crypto.randomUUID(), source_category: 'Salary', gross_amount: '', frequency: 'MONTHLY' }]); }
  async function remove(index) {
    const row = rows[index];
    if (row.income_id) {
      try { await api.deleteIncome(row.income_id); } catch (issue) { setErrors({ list: errorMessage(issue) }); return; }
    }
    setRows((current) => current.filter((_, i) => i !== index));
  }
  function submit(event) {
    event.preventDefault();
    const nextErrors = {};
    rows.forEach((row, i) => {
      if (!row.source_category?.trim()) nextErrors[`${i}-source`] = 'Choose an income source.';
      if (!(Number(row.gross_amount) > 0)) nextErrors[`${i}-amount`] = 'Enter an amount greater than zero.';
    });
    if (!rows.length) nextErrors.list = 'Add at least one source of income to continue.';
    setErrors(nextErrors);
    if (!Object.keys(nextErrors).length) onContinue(rows);
  }
  return <form className="wizard-form" onSubmit={submit}>
    <div className="wizard-section-intro"><h2>What is your primary source of income?</h2><p>Choose the closest match. You can add other sources below.</p></div>
    {rows.map((row, index) => <article className="wizard-entry-card" key={row.localId || row.income_id || index}>
      <div className="wizard-entry-head"><strong>{index === 0 ? 'Primary income' : `Additional income ${index}`}</strong>{rows.length > 1 && <button className="wizard-remove" type="button" onClick={() => remove(index)} aria-label={`Remove income source ${index + 1}`}><Trash2 size={16} /></button>}</div>
      <div className="wizard-fields-3">
        <Field label="Income source" error={errors[`${index}-source`]}><select value={row.source_category} onChange={(e) => update(index, 'source_category', e.target.value)}>{!incomeSources.includes(row.source_category) && <option value={row.source_category}>{row.source_category}</option>}{incomeSources.map((source) => <option key={source} value={source}>{source}</option>)}</select></Field>
        <Field label="How much do you earn? (₹)" error={errors[`${index}-amount`]}><input type="number" inputMode="decimal" min="0.01" step="0.01" value={row.gross_amount} onChange={(e) => update(index, 'gross_amount', e.target.value)} placeholder="e.g. 85,000" /></Field>
        <Field label="How often do you receive it?"><select value={row.frequency} onChange={(e) => update(index, 'frequency', e.target.value)}><option value="MONTHLY">Monthly</option><option value="YEARLY">Yearly</option></select></Field>
      </div>
    </article>)}
    {errors.list && <p className="field-error wizard-list-error">{errors.list}</p>}
    <button type="button" className="wizard-add" onClick={add}><CirclePlus size={17} />Add another income source</button>
    <p className="wizard-note">Monthly and yearly amounts are supported. Yearly income is converted to its monthly equivalent by the existing IntelliVest calculation.</p>
    <StepActions onBack={onBack} backLabel="Sign out" busy={busy} />
  </form>;
}

function ExpenseStep({ rows, setRows, busy, onBack, onContinue }) {
  const [errors, setErrors] = useState({});
  function update(index, key, value) { setRows((current) => current.map((row, i) => i === index ? { ...row, [key]: value } : row)); }
  function add() { setRows((current) => [...current, { localId: crypto.randomUUID(), category: 'Housing or rent', amount: '', recurrence_interval: 'MONTHLY', is_mandatory: null }]); }
  async function remove(index) {
    const row = rows[index];
    if (row.expense_id) {
      try { await api.deleteExpense(row.expense_id); } catch (e) { setErrors({ list: errorMessage(e) }); return; }
    }
    setRows((current) => current.filter((_, i) => i !== index));
  }
  function submit(event) {
    event.preventDefault(); const nextErrors = {};
    rows.forEach((row, i) => {
      if (!(Number(row.amount) > 0)) nextErrors[`${i}-amount`] = 'Enter an amount greater than zero.';
      if (row.is_mandatory !== true && row.is_mandatory !== false) nextErrors[`${i}-type`] = 'Choose necessary or optional.';
    });
    setErrors(nextErrors); if (!Object.keys(nextErrors).length) onContinue(rows);
  }
  return <form className="wizard-form" onSubmit={submit}>
    <div className="wizard-section-intro"><h2>Add the costs you pay regularly</h2><p>Necessary costs are essential commitments. Optional costs are flexible spending. You can leave this step empty if you have no recurring expenses.</p></div>
    {rows.map((row, index) => <article className="wizard-entry-card" key={row.localId || row.expense_id || index}>
      <div className="wizard-entry-head"><strong>{row.category || `Expense ${index + 1}`}</strong><button className="wizard-remove" type="button" onClick={() => remove(index)} aria-label={`Remove expense ${index + 1}`}><Trash2 size={16} /></button></div>
      <div className="wizard-fields-4">
        <Field label="Expense category"><select value={expenseCategories.includes(row.category) ? row.category : 'Other expenses'} onChange={(e) => update(index, 'category', e.target.value)}>{row.expense_id && !expenseCategories.includes(row.category) && <option value="Other expenses">Other expenses · {row.category}</option>}{expenseCategories.map((category) => <option key={category}>{category}</option>)}</select></Field>
        <Field label="Amount (₹)" error={errors[`${index}-amount`]}><input type="number" inputMode="decimal" min="0.01" step="0.01" value={row.amount} onChange={(e) => update(index, 'amount', e.target.value)} placeholder="e.g. 18,000" /></Field>
        <Field label="How often?"><select value={row.recurrence_interval} onChange={(e) => update(index, 'recurrence_interval', e.target.value)}><option value="MONTHLY">Monthly</option><option value="YEARLY">Yearly</option></select></Field>
        <Field label="Type" error={errors[`${index}-type`]}><select value={row.is_mandatory === null ? '' : row.is_mandatory ? 'necessary' : 'optional'} onChange={(e) => update(index, 'is_mandatory', e.target.value === '' ? null : e.target.value === 'necessary')}><option value="">Choose one</option><option value="necessary">Necessary</option><option value="optional">Optional</option></select></Field>
      </div>
    </article>)}
    {errors.list && <p className="field-error wizard-list-error">{errors.list}</p>}
    <button type="button" className="wizard-add" onClick={add}><CirclePlus size={17} />Add an expense</button>
    <p className="wizard-note">IntelliVest reports optional spending separately. The existing investable-surplus calculation subtracts necessary expenses and your chosen reserve.</p>
    <StepActions onBack={onBack} busy={busy} />
  </form>;
}

function SafetyStep({ user, summary, busy, onBack, onContinue }) {
  const [reserve, setReserve] = useState(String(summary?.liquid_safety_reserve ?? ''));
  const [tier, setTier] = useState(user.risk_tolerance_tier || 'MODERATE');
  const [errors, setErrors] = useState('');
  const options = [
    ['CONSERVATIVE', 'Conservative', 'I prefer protecting my money and limiting large losses.'],
    ['MODERATE', 'Moderate', 'I’m comfortable taking some risk for potential growth.'],
    ['AGGRESSIVE', 'Aggressive', 'I’m willing to accept larger fluctuations for potential higher returns.'],
  ];
  function submit(event) { event.preventDefault(); if (reserve === '' || Number(reserve) < 0 || !Number.isFinite(Number(reserve))) { setErrors('Enter a reserve amount of zero or more.'); return; } setErrors(''); onContinue(reserve, tier); }
  return <form className="wizard-form" onSubmit={submit}>
    <section className="safety-reserve-card"><div><span className="safety-icon"><ShieldCheck size={19} /></span><div><h2>Required cash reserve</h2><p>How much should stay available for emergencies before IntelliVest considers investments?</p></div></div><Field label="Reserve amount (₹)" error={errors}><input type="number" inputMode="decimal" min="0" step="0.01" value={reserve} onChange={(e) => setReserve(e.target.value)} /></Field></section>
    <div className="wizard-section-intro risk-choice-intro"><h2>How do you feel about investment risk?</h2><p>Your preference sets the starting recommendation capacity. Risk limits still apply.</p></div>
    <div className="risk-choice-grid">{options.map(([value, title, text]) => <button key={value} type="button" className={`risk-choice ${tier === value ? 'selected' : ''}`} aria-pressed={tier === value} onClick={() => setTier(value)}><span className="risk-choice-radio">{tier === value && <Check size={13} />}</span><strong>{title}</strong><span>{text}</span></button>)}</div>
    <p className="wizard-note">Other essential commitments belong in the expenses step. Don’t add those costs again here; only enter the cash amount you want held in reserve.</p>
    <StepActions onBack={onBack} busy={busy} continueLabel="Calculate my surplus" />
  </form>;
}

function EvaluationStep({ summary, busy, onBack, onEditIncome, onEditExpenses, onContinue }) {
  const positive = Number(summary?.investable_buffer || 0) > 0;
  return <div className="wizard-form">
    <div className="evaluation-hero"><span>Estimated investable surplus</span><strong>{money(summary?.investable_buffer)}</strong><p>{positive ? 'This is the amount available after the reserve you selected, subject to affordability and portfolio risk checks.' : 'Based on the information entered, no new investment is currently recommended. You can still continue to review your portfolio.'}</p></div>
    <section className="evaluation-breakdown"><h2>Monthly breakdown</h2><SummaryLine label="Income" value={summary?.monthly_income} /><SummaryLine label="Necessary expenses" value={summary?.monthly_mandatory_expenses} /><SummaryLine label="Optional expenses · shown separately" value={summary?.monthly_discretionary_expenses} /><SummaryLine label="Calculated surplus" value={summary?.computed_surplus} /><SummaryLine label="Cash reserve" value={summary?.liquid_safety_reserve} /><SummaryLine label="Estimated investable surplus" value={summary?.investable_buffer} strong /></section>
    <div className="evaluation-edit"><span>Need to change an answer?</span><div><button type="button" className="text-button" onClick={onEditIncome}>Edit income</button><button type="button" className="text-button" onClick={onEditExpenses}>Edit expenses</button></div></div>
    <p className="wizard-note">This summary comes from the IntelliVest backend. Optional expenses are displayed separately and are not deducted by the current surplus service.</p>
    <StepActions onBack={onBack} onContinue={onContinue} busy={busy} continueLabel="Continue to portfolio" />
  </div>;
}
function SummaryLine({ label, value, strong = false }) { return <div className={`evaluation-line ${strong ? 'strong' : ''}`}><span>{label}</span><strong>{money(value)}</strong></div>; }

function PortfolioStep({ user, savedPortfolios, busy, createdPortfolio, onCreated, onBack, onContinue, onError }) {
  const [choice, setChoice] = useState(savedPortfolios.length ? 'saved' : '');
  const [savedId, setSavedId] = useState(savedPortfolios[0]?.portfolio_id || '');
  const [name, setName] = useState('My portfolio');
  const [cash, setCash] = useState('0');
  const [drafts, setDrafts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState('');
  async function finish() {
    if (choice === 'saved') { if (!savedId) { setLocalError('Choose a saved portfolio to continue.'); return; } onContinue(savedId); return; }
    if (!name.trim()) { setLocalError('Enter a name for your portfolio.'); return; }
    if (choice === 'stocks' && (!drafts.length || drafts.some((d) => !d.security_id || !(Number(d.quantity) > 0) || !(Number(d.average_buy_price) > 0)))) {
      setLocalError('Select a market-listed security and enter its quantity and average purchase price for every holding.'); return;
    }
    if (choice === 'stocks' && new Set(drafts.map((d) => d.security_id)).size !== drafts.length) { setLocalError('Add each security once. Update its quantity if you own more shares.'); return; }
    setSaving(true); setLocalError(''); onError('');
    try {
      let portfolio = createdPortfolio;
      if (!portfolio) {
        portfolio = await api.createPortfolio({ user_id: user.user_id, portfolio_name: name.trim(), cash_balance: cash || '0' });
        onCreated(portfolio);
      }
      if (choice === 'stocks') {
        for (let i = 0; i < drafts.length; i += 1) {
          if (drafts[i].saved) continue;
          const result = await api.addHolding(portfolio.portfolio_id, { security_id: drafts[i].security_id, quantity: Number(drafts[i].quantity), average_buy_price: drafts[i].average_buy_price });
          setDrafts((current) => current.map((item, index) => index === i ? { ...item, saved: true, holding_id: result.holding_id } : item));
        }
      }
      onContinue(portfolio.portfolio_id);
    } catch (issue) { setLocalError(errorMessage(issue)); }
    finally { setSaving(false); }
  }
  function addHolding() { setDrafts((current) => [...current, { localId: crypto.randomUUID(), search: '', security_id: '', quantity: '1', average_buy_price: '', security: null, saved: false }]); }
  function updateHolding(index, change) { setDrafts((current) => current.map((d, i) => i === index ? { ...d, ...change } : d)); }
  return <div className="wizard-form">
    <div className="portfolio-choice-grid">
      <button type="button" className={`portfolio-choice ${choice === 'stocks' ? 'selected' : ''}`} aria-pressed={choice === 'stocks'} onClick={() => { setChoice('stocks'); setLocalError(''); }}><span className="portfolio-choice-icon"><Activity size={20} /></span><strong>Yes, I already own stocks</strong><span>Add market-listed holdings to include them in risk analysis.</span></button>
      <button type="button" className={`portfolio-choice ${choice === 'fresh' ? 'selected' : ''}`} aria-pressed={choice === 'fresh'} onClick={() => { setChoice('fresh'); setLocalError(''); }}><span className="portfolio-choice-icon"><ArrowRight size={20} /></span><strong>No, I’m starting fresh</strong><span>Continue with an empty portfolio and receive affordability-based ideas.</span></button>
    </div>
    {savedPortfolios.length > 0 && <section className="saved-portfolio-panel"><div><h2>Your saved portfolios</h2><p>Continue with an existing portfolio or create another one.</p></div><div className="saved-portfolio-list">{savedPortfolios.map((portfolio) => <label key={portfolio.portfolio_id} className={`saved-portfolio ${choice === 'saved' && savedId === portfolio.portfolio_id ? 'selected' : ''}`}><input type="radio" name="savedPortfolio" checked={choice === 'saved' && savedId === portfolio.portfolio_id} onChange={() => { setChoice('saved'); setSavedId(portfolio.portfolio_id); setLocalError(''); }} /><span><strong>{portfolio.portfolio_name}</strong><small>{money(portfolio.cash_balance)} cash balance</small></span></label>)}</div></section>}
    {(choice === 'stocks' || choice === 'fresh') && <section className="new-portfolio-panel">
      <div className="wizard-fields-2"><Field label="Portfolio name"><input maxLength="255" value={name} onChange={(e) => setName(e.target.value)} /></Field><Field label="Uninvested cash (₹)" hint="Only include cash held in this portfolio."><input type="number" min="0" step="0.01" value={cash} onChange={(e) => setCash(e.target.value)} /></Field></div>
      {choice === 'stocks' && <div className="holding-drafts"><div className="wizard-section-intro"><h2>Current holdings</h2><p>Search the IntelliVest security master. We’ll use its available market quote for valuation.</p></div>
        {drafts.map((draft, index) => <HoldingDraft key={draft.localId} value={draft} index={index} update={(change) => updateHolding(index, change)} remove={() => setDrafts((current) => current.filter((_, i) => i !== index))} />)}
        <button className="wizard-add" type="button" onClick={addHolding}><CirclePlus size={17} />Add another stock</button>
      </div>}
      {choice === 'fresh' && <p className="wizard-note">An empty portfolio has no fabricated holdings or historical risk metrics. You can add stocks later.</p>}
    </section>}
    {(localError || null) && <div className="wizard-error" role="alert">{localError}</div>}
    <div className="wizard-actions"><button className="button button-secondary" type="button" onClick={onBack} disabled={saving}><ArrowLeft size={16} />Back</button><button className="button button-primary" type="button" disabled={saving || (!choice && !savedPortfolios.length)} onClick={finish}>{saving ? <LoaderCircle className="spin" size={17} /> : null}{choice === 'saved' ? 'Use this portfolio' : 'Continue to analysis'}<ArrowRight size={16} /></button></div>
  </div>;
}

function HoldingDraft({ value, index, update, remove }) {
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  useEffect(() => {
    if (value.security) return;
    if (!value.search.trim()) { setResults([]); setSearching(false); return; }
    let live = true;
    const timer = setTimeout(async () => {
      setSearching(true); setSearchError('');
      try { const rows = await api.getSecurities(value.search || ''); if (live) setResults(rows); }
      catch (issue) { if (live) setSearchError(errorMessage(issue)); }
      finally { if (live) setSearching(false); }
    }, 250);
    return () => { live = false; clearTimeout(timer); };
  }, [value.search, value.security]);
  return <article className="holding-draft-card">
    <div className="wizard-entry-head"><strong>Stock {index + 1}</strong><button className="wizard-remove" type="button" onClick={remove} aria-label={`Remove stock ${index + 1}`}><Trash2 size={16} /></button></div>
    {!value.security ? <>
      <Field label="Search company or ticker"><span className="stock-search"><Search size={16} /><input value={value.search} onChange={(e) => update({ search: e.target.value })} placeholder="Search e.g. Infosys or INFY" /></span></Field>
      {searching && <p className="stock-search-status">Searching the security master…</p>}
      {searchError && <p className="field-error">{searchError}</p>}
      {!searching && value.search && !results.length && !searchError && <p className="stock-search-status">No quoted security matched. Check the name or ticker and try again.</p>}
      {results.length > 0 && <div className="security-results" role="listbox" aria-label="Market-listed securities">{results.slice(0, 8).map((row) => <button type="button" role="option" aria-selected="false" key={row.security_id} onClick={() => update({ security: row, security_id: row.security_id, search: `${row.company_name} (${row.ticker_symbol})` })}><span><strong>{row.company_name}</strong><small>{row.ticker_symbol} · {row.sector_name}</small></span><span className="security-quote">{money(row.latest_price)}<small>{row.price_date ? `As of ${new Date(row.price_date).toLocaleDateString('en-IN')}` : 'Quote date unavailable'}</small></span></button>)}</div>}
    </> : <div className="selected-security"><span><strong>{value.security.company_name}</strong><small>{value.security.ticker_symbol} · {value.security.sector_name} · latest quote {money(value.security.latest_price)} {value.security.price_date ? `as of ${new Date(value.security.price_date).toLocaleDateString('en-IN')}` : ''}</small></span><button type="button" className="text-button" onClick={() => update({ security: null, security_id: '', search: '', average_buy_price: '' })}>Change</button></div>}
    {value.security && <div className="wizard-fields-2"><Field label="Quantity owned"><input type="number" min="1" step="1" value={value.quantity} onChange={(e) => update({ quantity: e.target.value })} /></Field><Field label="Average purchase price (₹)" hint="Required to record your imported position; no transaction is created."><input type="number" min="0.01" step="0.01" value={value.average_buy_price} onChange={(e) => update({ average_buy_price: e.target.value })} placeholder="e.g. 1,450" /></Field></div>}
  </article>;
}

function AnalysisStep({ userId, preferredPortfolioId, summary, onBack, onDone }) {
  const [retry, setRetry] = useState(0);
  const [completed, setCompleted] = useState([]);
  const [skippedRisk, setSkippedRisk] = useState(false);
  const [error, setError] = useState('');
  const [running, setRunning] = useState(true);
  useEffect(() => {
    let alive = true;
    async function run() {
      setRunning(true); setError(''); setCompleted([]); setSkippedRisk(false);
      try {
        const [currentSummary, user, incomes, expenses, portfolios] = await Promise.all([
          api.getSummary(userId), api.getUser(userId), api.getIncome(userId), api.getExpenses(userId), api.getPortfolios(userId),
        ]);
        if (!alive) return;
        setCompleted(['profile']);
        const portfolioList = portfolios || [];
        const selected = portfolioList.find((row) => row.portfolio_id === preferredPortfolioId) || portfolioList[0];
        const [portfolio, holdings] = selected ? await Promise.all([
          api.getPortfolio(selected.portfolio_id), api.getHoldings(selected.portfolio_id),
        ]) : [null, []];
        if (!alive) return;
        setCompleted((current) => [...current, 'portfolio']);
        let risk = null;
        let alerts = [];
        if (portfolio && holdings.length) {
          risk = await api.getRisk(portfolio.portfolio_id);
          alerts = await api.getAlerts(portfolio.portfolio_id);
        } else {
          setSkippedRisk(true);
          alerts = portfolio ? await api.getAlerts(portfolio.portfolio_id) : [];
        }
        if (!alive) return;
        setCompleted((current) => [...current, 'risk']);
        let recommendations = await api.getRecommendations(userId);
        let generation = null;
        // The backend reuses the same batch when inputs are unchanged, replaces
        // stale pending advice when inputs changed, and records a zero-budget
        // outcome when the updated surplus no longer supports a recommendation.
        generation = await api.generateRecommendations(userId);
        recommendations = await api.getRecommendations(userId);
        if (!alive) return;
        setCompleted((current) => [...current, 'recommendations']);
        setRunning(false);
        await onDone({ profile: user, summary: currentSummary || summary, income: incomes, expenses, portfolios: portfolioList, portfolioId: portfolio?.portfolio_id || '', portfolio, holdings, risk, alerts, recommendations, generation });
      } catch (issue) { if (alive) { setRunning(false); setError(errorMessage(issue)); } }
    }
    run();
    return () => { alive = false; };
  }, [userId, preferredPortfolioId, retry]);
  const phases = [
    ['profile', 'Reviewing your financial profile', 'Loaded income, expenses, reserve, and risk preference.'],
    ['portfolio', 'Checking your portfolio', 'Loaded saved portfolios, holdings, and current valuation.'],
    ['risk', 'Evaluating investment risk', skippedRisk ? 'No holdings are available, so portfolio risk metrics are not calculated.' : 'Risk measures and portfolio alerts were returned by the backend.'],
    ['recommendations', 'Preparing your recommendations', 'Loaded existing ideas or generated a new affordable batch.'],
  ];
  return <div className="analysis-card" aria-live="polite">
    <div className="analysis-icon"><Activity size={22} /></div>
    <div className="analysis-phases">{phases.map(([id, title, detail]) => { const done = completed.includes(id); const active = running && !done && completed.length === phases.findIndex((item) => item[0] === id); return <div key={id} className={`analysis-phase ${done ? 'complete' : active ? 'active' : ''}`}><span className="analysis-phase-mark">{done ? <Check size={15} /> : active ? <LoaderCircle className="spin" size={15} /> : null}</span><div><strong>{title}</strong><small>{done ? detail : active ? 'Waiting for the service response…' : 'Next'}</small></div></div>; })}</div>
    {error && <div className="wizard-error analysis-error" role="alert"><strong>Analysis could not finish.</strong><span>{error}</span><button className="button button-secondary" type="button" onClick={() => setRetry((n) => n + 1)}><Activity size={15} />Retry analysis</button></div>}
    {!running && !error && <div className="analysis-complete"><Check size={17} />Your financial workspace is ready.</div>}
    <button className="wizard-back-link" type="button" onClick={onBack} disabled={running}><ArrowLeft size={15} />Back to portfolio setup</button>
  </div>;
}
