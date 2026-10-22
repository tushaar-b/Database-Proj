import { useEffect, useState } from 'react';
import { ArrowDown, ArrowUp } from 'lucide-react';
import './MarketTicker.css';

// Replace this illustrative local feed with the approved market-data API or WebSocket later.
const MOCK_MARKETS = [
  { name: 'NIFTY 50', price: 24823.15, change: 0.42 },
  { name: 'SENSEX', price: 81427.93, change: 0.36 },
  { name: 'BANK NIFTY', price: 51492.8, change: -0.18 },
  { name: 'NIFTY IT', price: 38652.4, change: 0.73 },
  { name: 'NIFTY MIDCAP', price: 58721.65, change: 0.21 },
  { name: 'NIFTY METAL', price: 9234.2, change: -0.31 },
];
const PRICE_FORMAT = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });

function TickerItem({ item }) {
  const isUp = item.change >= 0;
  const Direction = isUp ? ArrowUp : ArrowDown;
  return <div className="market-ticker__item">
    <span className="market-ticker__name">{item.name}</span>
    <strong className="market-ticker__price">{PRICE_FORMAT.format(item.price)}</strong>
    <span className={`market-ticker__change market-ticker__change--${isUp ? 'up' : 'down'}`}><Direction size={12} strokeWidth={2.5} />{isUp ? '+' : ''}{item.change.toFixed(2)}%</span>
  </div>;
}

export default function MarketTicker() {
  const [markets, setMarkets] = useState(MOCK_MARKETS);
  useEffect(() => {
    const timer = window.setInterval(() => {
      setMarkets((current) => current.map((item) => {
        const movement = (Math.random() - 0.5) * 0.0012;
        return { ...item, price: Math.max(0, item.price * (1 + movement)), change: item.change + movement * 100 };
      }));
    }, 4000);
    return () => window.clearInterval(timer);
  }, []);

  return <section className="market-ticker" id="markets" aria-label="Illustrative market index ticker">
    <div className="market-ticker__mask">
      <div className="market-ticker__track">
        {[0, 1].map((copy) => <div className="market-ticker__group" key={copy} aria-hidden={copy === 1}>
          {markets.map((item) => <TickerItem item={item} key={item.name} />)}
        </div>)}
      </div>
    </div>
    <span className="market-ticker__note">Illustrative market data</span>
  </section>;
}
