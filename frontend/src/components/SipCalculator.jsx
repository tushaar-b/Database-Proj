import useSectionReveal from '../hooks/useSectionReveal.js';
import MarketHistoryChart from './MarketHistoryChart.jsx';
import './SipCalculator.css';

// Reuse the existing two-column panel and its approved visual treatment.
// The chart reads public, explicitly classified research quotes; never personal portfolio data.
const context = [
  { title: 'Your existing holdings', copy: 'Record the stocks you already own, including quantities and purchase costs.' },
  { title: 'Value and diversification', copy: 'Review portfolio valuations from market data and how holdings are spread across sectors.' },
  { title: 'Risk alerts and feedback', copy: 'Configured risk-limit breaches can reduce allocation capacity or restrict sectors in future recommendations.' },
];
export default function RiskAnalytics() {
  const scope = useSectionReveal();
  return <section className="sip portfolio-risk-explanation" id="risk-analytics" ref={scope} aria-labelledby="risk-analytics-title"><div className="sip__inner">
    <div className="sip__heading" data-clay-reveal><span className="clay-badge">Portfolio intelligence</span><h2 id="risk-analytics-title">Put your portfolio risk in context.</h2><p>Understand your existing investments through valuations, historical risk measures and sector exposure.</p></div>
    <div className="sip__card clay-card" data-clay-reveal>
      <div className="sip__controls" id="how-it-works"><h3>Start with the stocks you own</h3>{context.map(({ title, copy }) => <div className="sip__control" key={title}><h4 className="sip__label">{title}</h4><p className="sip__assumptions">{copy}</p></div>)}<p className="sip__caveat">Your income, expenses, reserve and risk preference give recommendations their financial context.</p></div>
      <div className="sip__results"><MarketHistoryChart /></div>
    </div>
  </div></section>;
}
