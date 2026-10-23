import { ArrowDown, ArrowUp, Minus } from 'lucide-react';
import usePublicMarketData from '../hooks/usePublicMarketData.js';
import './MarketTicker.css';

const priceFormat = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
const quoteDate = (value) => new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`));

function PriceCard({ quote }) {
  const change = quote.change_percent == null ? null : Number(quote.change_percent);
  const direction = change == null || change === 0 ? 'neutral' : change > 0 ? 'up' : 'down';
  const Icon = direction === 'up' ? ArrowUp : direction === 'down' ? ArrowDown : Minus;
  return <div className="market-ticker__item" title={quote.company_name}>
    <span className="market-ticker__name">{quote.ticker}</span>
    <strong className="market-ticker__price">{priceFormat.format(Number(quote.close_price))}</strong>
    <span className={`market-ticker__change market-ticker__change--${direction}`} title={quote.previous_date ? `Compared with the stored close on ${quoteDate(quote.previous_date)}` : 'No previous closing price available'}><Icon size={12} aria-hidden="true" />{change == null ? 'No comparison' : `${change > 0 ? '+' : ''}${change.toFixed(2)}%`}</span>
    <span className="market-ticker__date">Stored close · {quoteDate(quote.price_date)}</span>
  </div>;
}

export default function MarketTicker() {
  const { status, data, error, retry } = usePublicMarketData('/securities?limit=50');
  const quotes = data?.securities?.slice(0, 6) || [];
  return <section className="market-ticker price-ticker" aria-label="Illustrative research price ticker">
    <div className="market-ticker__mask" tabIndex={0} role="region" aria-label="Scroll stored equity research prices" aria-busy={status === 'loading'}>
      {status === 'loading' ? <div className="market-ticker__group" role="status">{Array.from({ length: 6 }, (_, index) => <div className="market-ticker__item price-ticker__placeholder" key={index} aria-hidden={index > 0}><span className="market-ticker__name">Loading research quotes…</span><strong>—</strong></div>)}</div>
        : status === 'error' || !quotes.length ? <div className="price-ticker__unavailable" role="status"><span>{error || 'No stored equity quotes are available yet.'}</span><button type="button" className="clay-btn clay-btn--soft" onClick={retry}>Retry prices</button></div>
          : <div className="market-ticker__track">{[0, 1].map((copy) => <div className="market-ticker__group" key={copy} aria-hidden={copy === 1}>{quotes.map((quote) => <PriceCard key={quote.ticker} quote={quote} />)}</div>)}</div>}
    </div>
    <span className="market-ticker__note">Illustrative research data · source unverified; may include synthetic quotes · not live prices. Changes compare consecutive stored, unadjusted closes.</span>
  </section>;
}
