import { useId, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { RefreshCw } from 'lucide-react';
import usePublicMarketData from '../hooks/usePublicMarketData.js';
import useReducedMotion from '../hooks/useReducedMotion.js';
import './MarketHistoryChart.css';

const DAY = 86400000;
const ranges = [{ label: '1M', days: 30 }, { label: '3M', days: 90 }, { label: '6M', days: 180 }, { label: '1Y', days: 365 }];
const timestamp = (value) => Date.parse(`${value}T00:00:00Z`);
const formatDate = (value, withYear = false) => new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', ...(withYear ? { year: 'numeric' } : {}), timeZone: 'UTC' }).format(new Date(value));
const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });

function PriceTooltip({ active, payload }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;
  return <div className="market-history__tooltip"><strong>{formatDate(point.timestamp, true)}</strong><span>Research close <b>{currency.format(point.close)}</b></span><small>Source unverified · not live</small></div>;
}

export default function MarketHistoryChart() {
  const catalogue = usePublicMarketData('/securities?limit=50');
  const [ticker, setTicker] = useState('');
  const [requestedDays, setRequestedDays] = useState(365);
  const securities = catalogue.data?.securities || [];
  const selected = securities.find((security) => security.ticker === ticker) || securities[0];
  const history = usePublicMarketData(selected ? `/securities/${encodeURIComponent(selected.ticker)}/history` : null);
  const reducedMotion = useReducedMotion();
  const chartId = `market-history-${useId().replace(/:/g, '')}`;
  const points = useMemo(() => (history.data?.points || []).map((point) => ({ timestamp: timestamp(point.date), close: Number(point.close) })).filter((point) => Number.isFinite(point.timestamp) && Number.isFinite(point.close)), [history.data]);
  const asOf = history.data ? timestamp(history.data.as_of) : null;
  const coverage = history.data ? (asOf - timestamp(history.data.history_start)) / DAY : 0;
  const availableRanges = ranges.filter((range) => coverage >= range.days && points.filter((point) => point.timestamp >= asOf - range.days * DAY).length >= 2);
  const days = availableRanges.some((range) => range.days === requestedDays) ? requestedDays : availableRanges.at(-1)?.days || null;
  const visible = useMemo(() => days == null ? points : points.filter((point) => point.timestamp >= asOf - days * DAY), [points, asOf, days]);
  const error = catalogue.status === 'error' ? catalogue.error : history.status === 'error' ? history.error : null;
  const loading = catalogue.status === 'loading' || (selected && history.status === 'loading');
  const last = visible.at(-1);
  const retry = () => catalogue.status === 'error' || !securities.length ? catalogue.retry() : history.retry();

  return <section className="market-history" aria-labelledby={`${chartId}-title`}>
    <div className="market-history__heading"><div><span className="clay-badge">Illustrative research data</span><h3 id={`${chartId}-title`}>Explore stored price movements</h3></div><button type="button" className="market-history__refresh" aria-label="Refresh stored price history" onClick={retry} disabled={Boolean(loading)}><RefreshCw size={16} /></button></div>
    <p className="market-history__classification">Source unverified; may include synthetic quotes. These are not live or verified historical market prices.</p>
    <div className="market-history__controls"><label htmlFor={`${chartId}-security`}>Security<select id={`${chartId}-security`} value={selected?.ticker || ''} onChange={(event) => setTicker(event.target.value)} disabled={catalogue.status !== 'ready' || !securities.length}>{!securities.length && <option value="">{catalogue.status === 'loading' ? 'Loading securities…' : 'No securities available'}</option>}{securities.map((security) => <option value={security.ticker} key={security.ticker}>{security.ticker} · {security.company_name}</option>)}</select></label>
      <div className="market-history__ranges" role="group" aria-label="Trailing period from the latest stored date">{ranges.map((range) => <button type="button" key={range.label} aria-pressed={days === range.days} disabled={!availableRanges.some((available) => available.days === range.days)} title={`${range.days} calendar days ending on the latest stored date; disabled when full coverage is unavailable`} onClick={() => setRequestedDays(range.days)}>{range.label}</button>)}{history.data && !availableRanges.length && <span>Available history</span>}</div>
    </div>
    <div className="market-history__summary" aria-live="polite">{last ? <><strong>{currency.format(last.close)}</strong><span>Stored close · {formatDate(last.timestamp, true)}</span></> : <span>{loading ? 'Loading stored closing prices…' : 'No closing price available'}</span>}</div>
    <div className="market-history__plot" aria-busy={Boolean(loading)}>
      {loading ? <div className="market-history__state" role="status">Loading stored price history…</div>
        : error || visible.length < 2 ? <div className="market-history__state" role="status"><p>{error || 'At least two stored observations are needed to display this series.'}</p><button type="button" className="clay-btn clay-btn--soft" onClick={retry}>Retry history</button></div>
          : <ResponsiveContainer width="100%" height="100%"><AreaChart data={visible} margin={{ top: 12, right: 12, left: 2, bottom: 24 }} accessibilityLayer>
            <defs><linearGradient id={`${chartId}-fill`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--lilac-200)" stopOpacity={.75} /><stop offset="1" stopColor="var(--lilac-100)" stopOpacity={.12} /></linearGradient></defs>
            <CartesianGrid stroke="var(--peach-300)" strokeDasharray="4 6" vertical={false} />
            <XAxis dataKey="timestamp" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={(value) => formatDate(value)} minTickGap={28} tick={{ fill: 'var(--plum-500)', fontSize: 10 }} axisLine={false} tickLine={false} label={{ value: 'Stored date', position: 'bottom', offset: 8, fill: 'var(--plum-500)', fontSize: 10 }} />
            <YAxis domain={['auto', 'auto']} width={64} tickFormatter={(value) => `₹${new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(value)}`} tick={{ fill: 'var(--plum-500)', fontSize: 10 }} axisLine={false} tickLine={false} label={{ value: 'Close (INR)', angle: -90, position: 'insideLeft', fill: 'var(--plum-500)', fontSize: 10 }} />
            <Tooltip content={<PriceTooltip />} allowEscapeViewBox={{ x: false, y: false }} wrapperStyle={{ maxWidth: '100%', pointerEvents: 'none' }} cursor={{ stroke: 'var(--plum-500)', strokeDasharray: '4 4' }} />
            <Area type="linear" dataKey="close" name="Stored research close" stroke="var(--indigo)" fill={`url(#${chartId}-fill)`} strokeWidth={2.5} dot={false} activeDot={{ r: 4, stroke: 'var(--cream-50)', strokeWidth: 2 }} isAnimationActive={!reducedMotion} animationDuration={450} />
          </AreaChart></ResponsiveContainer>}
    </div>
    <p className="market-history__caption">{visible.length > 0 && `${formatDate(visible[0].timestamp, true)} – ${formatDate(last.timestamp, true)} · ${visible.length} observations. `}Ranges cover 30, 90, 180 or 365 calendar days before the latest stored date. Unadjusted closes may reflect corporate actions.</p>
    <p className="market-history__caption">Price variation illustrates volatility and downside exposure; it does not predict future prices or measure your personal portfolio risk. Securities are listed alphabetically, not as recommendations.</p>
  </section>;
}
