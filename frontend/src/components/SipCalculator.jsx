import { useId, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import useSectionReveal from '../hooks/useSectionReveal.js';
import './SipCalculator.css';

const rupees = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const controls = [
  { key: 'monthly', label: 'Monthly investment', min: 500, max: 100000, step: 500, format: (v) => rupees.format(v) },
  { key: 'years', label: 'Investment period', min: 1, max: 40, step: 1, format: (v) => `${v} years` },
  { key: 'rate', label: 'Expected annual return', min: 0, max: 25, step: .5, format: (v) => `${v}%` },
];
// Illustrative annuity-due calculation only; never used by advisory or surplus services.
function futureValue(monthly, months, monthlyRate) {
  return monthlyRate === 0 ? monthly * months : monthly * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) * (1 + monthlyRate);
}
function SipTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="sip__tooltip clay-tooltip"><strong>Year {label}</strong>{payload.map((row) => <p key={row.dataKey}><span>{row.name}</span><b>{rupees.format(row.value)}</b></p>)}</div>;
}
export default function SipCalculator() {
  const scope = useSectionReveal();
  const chartId = `sip-${useId().replace(/:/g, '')}`;
  const [values, setValues] = useState({ monthly: 5000, years: 10, rate: 12 });
  const data = useMemo(() => Array.from({ length: values.years + 1 }, (_, year) => ({ year, invested: values.monthly * year * 12, estimated: futureValue(values.monthly, year * 12, values.rate / 1200) })), [values]);
  const final = data[data.length - 1];
  return <section className="sip" id="sip-calculator" ref={scope} aria-labelledby="sip-title"><div className="sip__inner">
    <div className="sip__heading" data-clay-reveal><span className="clay-badge">Picture the possibilities</span><h2 id="sip-title">Small steps. A longer view.</h2><p>Explore how regular contributions could add up over time.</p></div>
    <div className="sip__card clay-card" data-clay-reveal><div className="sip__controls"><h3>Your SIP illustration</h3>{controls.map(({ key, label, min, max, step, format }) => <div className="sip__control" key={key}><div className="sip__label"><label htmlFor={`${chartId}-${key}`}>{label}</label><output htmlFor={`${chartId}-${key}`}>{format(values[key])}</output></div><input id={`${chartId}-${key}`} type="range" min={min} max={max} step={step} value={values[key]} aria-valuetext={format(values[key])} onChange={(e) => setValues((v) => ({ ...v, [key]: Number(e.target.value) }))} /><div className="sip__range-ends" aria-hidden="true"><span>{format(min)}</span><span>{format(max)}</span></div></div>)}<p className="sip__caveat">Illustrative only. Not a guarantee of returns.</p></div>
      <div className="sip__results"><dl className="sip__totals"><div><dt>Invested amount</dt><dd>{rupees.format(final.invested)}</dd></div><div><dt>Estimated value</dt><dd>{rupees.format(final.estimated)}</dd></div><div><dt>Estimated gain</dt><dd>{rupees.format(final.estimated - final.invested)}</dd></div></dl>
        <div className="sip__chart" role="img" aria-label={`SIP illustration over ${values.years} years: invested ${rupees.format(final.invested)}, estimated value ${rupees.format(final.estimated)}.`}><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 15, right: 12, bottom: 8, left: 0 }}><defs><linearGradient id={`${chartId}-invested`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--lilac-200)" stopOpacity={.9} /><stop offset="1" stopColor="var(--lilac-100)" stopOpacity={.25} /></linearGradient><linearGradient id={`${chartId}-estimated`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--coral)" stopOpacity={.55} /><stop offset="1" stopColor="var(--sun)" stopOpacity={.12} /></linearGradient></defs><CartesianGrid stroke="var(--peach-300)" strokeDasharray="4 6" vertical={false} /><XAxis dataKey="year" minTickGap={22} axisLine={false} tickLine={false} tick={{ fill: 'var(--plum-500)', fontSize: 11 }} tickFormatter={(v) => `${v}y`} /><YAxis width={64} axisLine={false} tickLine={false} tick={{ fill: 'var(--plum-500)', fontSize: 10 }} tickFormatter={(v) => v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` : `₹${(v / 1000).toFixed(0)}k`} /><Tooltip content={<SipTooltip />} cursor={{ stroke: 'var(--plum-500)', strokeDasharray: '4 4' }} /><Area type="monotone" dataKey="estimated" name="Estimated value" stroke="var(--coral-600)" fill={`url(#${chartId}-estimated)`} strokeWidth={3} isAnimationActive={false} /><Area type="monotone" dataKey="invested" name="Invested amount" stroke="var(--violet)" fill={`url(#${chartId}-invested)`} strokeWidth={2} isAnimationActive={false} /></AreaChart></ResponsiveContainer></div>
        <div className="sip__legend"><span><i />Invested amount</span><span><i />Estimated value</span></div><p className="sip__assumptions">Assumes a constant annual return, compounded monthly, with contributions at the start of each month. Excludes fees, taxes and inflation. Actual returns fluctuate and may be negative.</p>
      </div></div>
  </div></section>;
}
