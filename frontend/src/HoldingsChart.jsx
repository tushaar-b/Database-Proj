import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
const compact = (value) => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function HoldingsChart({ holdings }) {
  const data = holdings.filter((item) => item.market_value != null).map((item) => ({ ticker: item.ticker_symbol, value: Number(item.market_value) }));
  if (!data.length) return null;
  return <section className="panel chart-panel"><div className="panel-heading"><div><p className="eyebrow">Current holdings</p><h2>Market value by security</h2></div><span className="chart-caption">Latest available quotes</span></div><div className="holdings-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout="vertical" margin={{ left: 10, right: 24, top: 4, bottom: 4 }}><CartesianGrid stroke="#E2E8F0" horizontal={false} /><XAxis type="number" tickFormatter={(value) => `₹${compact(value)}`} tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="ticker" width={66} tick={{ fill: '#334155', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} /><Tooltip formatter={(value) => [currency.format(Number(value)), 'Market value']} contentStyle={{ borderRadius: 10, border: '1px solid #E2E8F0', fontFamily: 'inherit' }} /><Bar dataKey="value" fill="#2563EB" radius={[0, 7, 7, 0]} barSize={22} /></BarChart></ResponsiveContainer></div></section>;
}
