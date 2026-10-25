import './RecentMarketTrend.css';
const pct = v => v == null ? 'Unavailable' : `${(Number(v) * 100).toFixed(2)}%`;
const money = v => v == null ? 'Unavailable' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(v));
const position = v => ({ positive: 'above', negative: 'below', approximately_flat: 'near (within tolerance)' }[v] || 'unavailable');
const score = v => v == null ? 'Unavailable' : Number(v).toFixed(8);

export function TrendBadge({ evidence }) {
  const t = evidence?.trend;
  if (!t) return <span className="trend-badge trend-badge--unavailable">Trend not assessed</span>;
  const weak = t.status === 'available' && t.warning;
  return <span className={`trend-badge trend-badge--${t.status !== 'available' ? 'unavailable' : weak ? 'negative' : t.classification === 'Positive Momentum' ? 'positive' : 'mixed'}`} title={`Saved assessment as of ${t.as_of || 'unknown'}; historical signals, not forecasts.`}>
    {t.status !== 'available' ? 'Trend data limited' : weak ? 'Recent weakness' : t.classification === 'Positive Momentum' ? 'Positive trend' : 'Mixed trend'}
  </span>;
}

export default function RecentMarketTrend({ trend, evidence, saved = false }) {
  const t = trend || evidence?.trend;
  if (!t) return <section className="recent-market-trend"><h3>Recent Market Trend</h3><p>No trend evidence was recorded for this older decision. Check for updates to generate a trend-aware batch. Its historical explanation has been preserved.</p></section>;
  const available = t.status === 'available';
  return <section className={`recent-market-trend${t.warning ? ' recent-market-trend--warning' : ''}`}>
    <p className="trend-context">{saved ? 'Recorded at recommendation time' : 'Current historical assessment · independent of the selected chart range'}</p>
    <h3>{available && t.warning ? 'Recent Price Weakness Detected' : 'Recent Market Trend'}</h3>
    <p><strong>{t.classification}</strong> · observations through {t.as_of || 'unavailable'} · {t.source} · adjusted daily closes.</p>
    {!available && <p role="status">{t.issues?.join(' ')} Any numeric values below describe the dated observations only; they are not a fresh or neutral assessment.</p>}
    <p>20-session return window: {t.return20_start || 'unavailable'} to {t.as_of || 'unavailable'}; 60-session window: {t.return60_start || 'unavailable'} to {t.as_of || 'unavailable'}.</p>
    <dl className="trend-values">
      <div><dt>20-session return</dt><dd>{pct(t.return20)}</dd></div><div><dt>60-session return</dt><dd>{pct(t.return60)}</dd></div>
      <div><dt>20-session average</dt><dd>{money(t.ma20)}</dd></div><div><dt>50-session average</dt><dd>{money(t.ma50)}</dd></div>
      <div><dt>Last adjusted close</dt><dd>{money(t.adjusted_close)}</dd></div><div><dt>Weakness indicators</dt><dd>{t.negative_votes == null ? 'Unavailable' : `${t.negative_votes} / 5`}</dd></div>
    </dl>
    <p>Price versus 20-session average: {position(t.relations?.price_vs_ma20)}; versus 50-session average: {position(t.relations?.price_vs_ma50)}. 20-session average versus 50-session average: {position(t.relations?.ma20_vs_ma50)}.</p>
    {evidence && <><p>{evidence.penalty_type === 'data_quality_uncertainty' ? 'Unavailable trend evidence received an explicit data-quality uncertainty penalty.' : Number(evidence.momentum_penalty) > 0 ? 'A momentum penalty reduced this candidate’s score.' : 'No negative-momentum penalty was applied.'} Falling prices alone do not disqualify a security. It remained eligible under holdings, sector and risk policy, ranked competitively within the sector-priority order, and passed the saved whole-share affordability checks.</p><dl className="trend-values"><div><dt>Baseline daily score</dt><dd>{score(evidence.baseline_score)}</dd></div><div><dt>Daily penalty</dt><dd>{score(evidence.momentum_penalty)}</dd></div><div><dt>Adjusted daily score</dt><dd>{score(evidence.selection_score)}</dd></div></dl></>}
    <details><summary>What do these signals mean, and how are they calculated?</summary>
      <p>Recent momentum describes past price direction. Comparing recent and longer windows helps identify disagreement with longer-term return statistics; it does not predict future direction or establish undervaluation.</p>
      <p>R20 = adjusted close / adjusted close 20 observed sessions earlier − 1; R60 uses 60 sessions earlier. Returns above are percentages. MA20 and MA50 are arithmetic averages of the latest 20 and 50 completed adjusted closes, in INR. No intraday price is inserted.</p>
      <p>Five signals compare R20, R60, price/MA20, price/MA50 and MA20/MA50. Flat-return bands: {pct(t.policy?.flat_return_20)} and {pct(t.policy?.flat_return_60)}; moving-average tolerance: {pct(t.policy?.ma_tolerance)}. Strong negative momentum requires at least a {pct(t.policy?.strong_decline_20)} 20-session decline, {t.policy?.strong_votes_required} weakness signals, price below MA50 and MA20 below MA50. Negative requires {t.policy?.negative_votes_required} weakness signals and a negative recent return. Positive requires {t.policy?.positive_votes_required} positive signals, positive R20 and R60 not below its negative flat band. Other fully supported cases are mixed.</p>
      <p>For ranking, 20/60-session declines and the price/MA50 shortfall become daily geometric equivalents, divided by daily volatility and capped at {t.policy?.severity_cap} daily-volatility units. Weights: {t.policy?.weights?.map(pct).join(' / ')}. Agreement multiplier = 1 + {t.policy?.agreement_strength} × negative signals / 5. Daily penalty = tier weight × daily volatility × weighted severity. Unknown trend data use a separately disclosed severity of {t.policy?.unknown_severity}; missing returns are never set to zero.</p>
      {evidence && <p>Saved investor preference: {evidence.risk_tier}; momentum tier weight: {evidence.momentum_tier_coefficient}. Historical baseline uses up to {evidence.observations} daily returns: mean − risk aversion × (sample volatility + historical one-day CVaR95). History: {evidence.history_start} to {evidence.history_through}, source {evidence.history_source}. Method: {evidence.methodology_version}. These are configurable research rules; comparative investment-performance improvement has not been established.</p>}
    </details>
  </section>;
}
