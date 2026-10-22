import Logo from './Logo.jsx';
import './Footer.css';
const columns = [
  { title: 'Stocks', links: [['Market overview', '#markets'], ['Portfolio research', '#features']] },
  { title: 'F&O', links: [['Market context', '#markets'], ['Explore products', '#products']] },
  { title: 'Mutual Funds', links: [['SIP calculator', '#sip-calculator'], ['Investing approach', '#features']] },
  { title: 'More', links: [['About Intellivest', '#about'], ['IPOs & ETFs', '#products']] },
];
export default function Footer() {
  return <footer className="footer"><div className="clay-divider footer__wave" aria-hidden="true" /><div className="footer__inner"><div className="footer__top"><div className="footer__brand"><Logo className="brand-logo--dusk" /><p>A little more clarity.<br />A thoughtful way to explore investing.</p></div><nav className="footer__links" aria-label="Footer navigation">{columns.map(({ title, links }) => <div key={title}><h2>{title}</h2>{links.map(([label, href]) => <a href={href} key={label}>{label}</a>)}</div>)}</nav></div>
    <div className="footer__bottom"><p>Investments in securities markets are subject to market risks. Read all related documents carefully before investing.</p><p>Intellivest is an advisory and analytics platform. It does not execute trades or provide brokerage services. Market ticker values are illustrative.</p>{/* TODO: Fill in and verify legal entity and registration details before launch. */}<small>© {new Date().getFullYear()} Intellivest</small></div>
  </div></footer>;
}
