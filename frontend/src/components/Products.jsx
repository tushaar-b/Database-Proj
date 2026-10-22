import { ArrowRight, LineChart, Layers, Activity } from 'lucide-react';
import useSectionReveal from '../hooks/useSectionReveal.js';
import './Products.css';

const products = [
  { name: 'Stocks', icon: LineChart, tint: 'lilac', copy: 'Explore companies, understand your holdings, and put portfolio risk in context.', href: '#markets' },
  { name: 'Mutual Funds', icon: Layers, tint: 'mint', copy: 'Explore the shape of long-term investing with a simple SIP illustration.', href: '#sip-calculator' },
  { name: 'F&O', icon: Activity, tint: 'coral', copy: 'Start with an understanding of market movement. Derivatives can carry substantial risk.', href: '#markets' },
];
export default function Products() {
  const scope = useSectionReveal();
  return <section className="products" id="products" ref={scope} aria-labelledby="products-title"><div className="products__inner">
    <div className="products__heading" data-clay-reveal><div><span className="clay-badge">Room for your curiosity</span><h2 id="products-title">Your world of investing.</h2></div><span className="clay-chip">IPOs</span></div>
    <div className="products__grid">{products.map(({ name, icon: Icon, tint, copy, href }) => <article className={`products__card clay-card clay-card--${tint}`} key={name} data-clay-reveal><Icon className="products__icon" size={44} strokeWidth={1.6} aria-hidden="true" /><h3>{name}</h3><p>{copy}</p><a className="clay-btn clay-btn--soft" href={href} aria-label={`Learn more about ${name}`}>Learn more <ArrowRight size={16} /></a></article>)}</div>
    <p className="products__note" data-clay-reveal>Intellivest provides advisory and portfolio analytics. It does not execute trades or open brokerage accounts. Product information and calculators are for exploration.</p>
  </div></section>;
}
