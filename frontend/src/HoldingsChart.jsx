import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(value));
const number = (value, digits = 2) => Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits });

function HoldingsTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="clay-tooltip"><strong>{label}</strong><p>Market value: {money(payload[0].value)}</p></div>;
}

export default function HoldingsChart({ holdings }) {
  const data = holdings.filter((item) => item.market_value != null).map((item) => ({ ticker: item.ticker_symbol, value: Number(item.market_value) }));
  if (!data.length) return null;
  return <section className="panel chart-panel"><div className="panel-heading"><div><p className="eyebrow">Current holdings</p><h2>Market value by security</h2></div><span className="chart-caption">Latest available quotes</span></div><div className="holdings-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout="vertical" margin={{ left: 10, right: 24, top: 4, bottom: 4 }}><CartesianGrid stroke="var(--peach-300)" strokeDasharray="4 6" horizontal={false} /><XAxis type="number" tickFormatter={(value) => `₹${number(value, 0)}`} tick={{ fill: 'var(--plum-500)', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="ticker" width={66} tick={{ fill: 'var(--plum-700)', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} /><Tooltip content={<HoldingsTooltip />} cursor={{ fill: 'var(--lilac-100)' }} /><Bar dataKey="value" fill="var(--indigo)" radius={[0, 12, 12, 0]} barSize={22} /></BarChart></ResponsiveContainer></div></section>;
}

