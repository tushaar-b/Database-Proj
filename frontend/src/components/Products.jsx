import { Wallet, Layers, LineChart } from 'lucide-react';
import useSectionReveal from '../hooks/useSectionReveal.js';
import TiltedFeatureGrid from './TiltedFeatureGrid.jsx';
import './Products.css';

const products = [
  { id: 'financial-overview', name: 'Know your investable amount', icon: Wallet, tint: 'lilac', copy: 'Bring your income, expenses and savings together to understand what is available for investing.', action: 'Get started' },
  { id: 'portfolio-analytics', name: 'Understand your portfolio', icon: Layers, tint: 'mint', copy: 'Add the stocks you already own and explore portfolio value, diversification and historical risk.', action: 'Learn more', href: '#risk-analytics' },
  { id: 'stock-recommendations', name: 'Discover stock recommendations', icon: LineChart, tint: 'coral', copy: 'Explore stock suggestions based on your available budget, risk preference and current portfolio exposure.', action: 'Get started' },
];
export default function Products({ onGetStarted }) {
  const scope = useSectionReveal();
  return <section className="products" id="features" ref={scope} aria-labelledby="products-title"><div className="products__inner">
    <div className="products__heading" data-clay-reveal><div><span className="clay-badge">Room for your curiosity</span><h2 id="products-title">Everything you need to invest more thoughtfully.</h2><p className="products__description">From understanding your finances to reviewing portfolio risk, IntelliVest brings the important decisions together.</p></div></div>
    <TiltedFeatureGrid features={products} onGetStarted={onGetStarted} />
    <p className="products__note" data-clay-reveal>IntelliVest is a research and financial decision-support platform. It does not execute stock trades or provide brokerage services.</p>
  </div></section>;
}
