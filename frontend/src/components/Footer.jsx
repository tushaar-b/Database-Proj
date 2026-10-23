import Logo from './Logo.jsx';
import './Footer.css';
const columns = [
  { title: 'Platform', links: [['Financial Overview', '#financial-overview'], ['Stock Recommendations', '#stock-recommendations'], ['Portfolio Analytics', '#portfolio-analytics']] },
  { title: 'Features', links: [['Investable Surplus', '#investable-surplus'], ['Portfolio Risk', '#risk-analytics'], ['Risk Alerts', '#risk-alerts']] },
  { title: 'Explore', links: [['How It Works', '#how-it-works'], ['Why IntelliVest', '#why-intellivest'], ['Get Started', '#get-started']] },
];
export default function Footer() {
  return <footer className="footer" id="about"><div className="clay-divider footer__wave" aria-hidden="true" /><div className="footer__inner"><div className="footer__top"><div className="footer__brand"><Logo className="brand-logo--dusk" /><p>Understand your finances. Explore your investments. Make more informed decisions.</p></div><nav className="footer__links" aria-label="Footer navigation">{columns.map(({ title, links }) => <div key={title}><h2>{title}</h2>{links.map(([label, href]) => <a href={href} key={label}>{label}</a>)}</div>)}</nav></div>
    <div className="footer__bottom"><p>Investments in securities markets are subject to market risk. Historical performance and risk estimates do not guarantee future results.</p><p>IntelliVest is a financial research and decision-support platform. It does not execute trades or operate brokerage accounts.</p><small>© {new Date().getFullYear()} Intellivest</small></div>
  </div></footer>;
}
