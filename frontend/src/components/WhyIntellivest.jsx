import { Wallet, ShieldCheck, LineChart, RefreshCw } from 'lucide-react';
import useSectionReveal from '../hooks/useSectionReveal.js';
import ClayBlob from './ClayBlob.jsx';
import FeatureShowcase from './FeatureShowcase.jsx';
import './WhyIntellivest.css';

const reasons = [
  { id: 'investable-surplus', icon: Wallet, title: 'Invest within your means', copy: 'Understand how much money you can realistically invest after accounting for income, expenses and financial reserves.', tint: 'lilac' },
  { id: 'portfolio-risk', icon: ShieldCheck, title: 'Understand your portfolio risk', copy: 'See what VaR, CVaR, volatility and sector concentration reveal about your existing investments.', tint: 'mint' },
  { id: 'recommendations-with-context', icon: LineChart, title: 'Recommendations with context', copy: 'Explore stock suggestions that consider affordability, existing holdings and your comfort with risk.', tint: 'coral' },
  { id: 'risk-alerts', icon: RefreshCw, title: 'Advice that adapts', copy: 'When your portfolio changes or risk limits are crossed, IntelliVest updates the constraints behind future recommendations.', tint: 'sun' },
];
export default function WhyIntellivest() {
  const scope = useSectionReveal();
  return <section className="why" id="why-intellivest" ref={scope} aria-labelledby="why-title">
    <ClayBlob tint="mint" className="why__blob" />
    <div className="why__inner">
      <div className="why__heading" data-clay-reveal><span className="clay-badge">A little more perspective</span><h2 id="why-title">Why IntelliVest</h2><p>A clearer way to connect your financial situation with smarter stock investment decisions.</p></div>
      <FeatureShowcase features={reasons} />
    </div>
  </section>;
}
