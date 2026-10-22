import { useRef, useState } from 'react';
import { ChevronDown, Menu, X } from 'lucide-react';
import Logo from './Logo.jsx';
import SearchBar from './SearchBar.jsx';
import './Navbar.css';

const primaryLinks = [
  { label: 'Stocks', href: '#markets' },
  { label: 'F&O', href: '#markets' },
  { label: 'Mutual Funds', href: '#features' },
];
const moreLinks = [
  { label: 'IPOs & ETFs', href: '#features' },
  { label: 'Market indices', href: '#markets' },
  { label: 'About Intellivest', href: '#about' },
];

export default function Navbar({ onLogin }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const mobileSearchRef = useRef(null);
  const desktopSearchRef = useRef(null);
  const closeMenus = () => { setMobileOpen(false); setMoreOpen(false); };

  return <header className="site-navbar">
    <div className="site-navbar__inner">
      <Logo />
      <nav className={`site-navbar__links ${mobileOpen ? 'site-navbar__links--open' : ''}`} aria-label="Main navigation">
        {primaryLinks.map((item) => <a key={item.label} href={item.href} onClick={closeMenus}>{item.label}</a>)}
        <span className="site-navbar__divider" aria-hidden="true" />
        <div className="site-navbar__more">
          <button className="site-navbar__more-button" type="button" aria-expanded={moreOpen} onClick={() => setMoreOpen((open) => !open)}>More <ChevronDown size={14} /></button>
          {moreOpen && <div className="site-navbar__dropdown clay-dropdown">{moreLinks.map((item) => <a key={item.label} href={item.href} onClick={closeMenus}>{item.label}</a>)}</div>}
        </div>
        <div className="site-navbar__mobile-search"><SearchBar ref={mobileSearchRef} /></div>
        <div className="site-navbar__tools"><SearchBar ref={desktopSearchRef} /><button className="site-navbar__login clay-btn clay-btn--dark" type="button" onClick={() => { closeMenus(); onLogin(); }}>Login / Sign up</button></div>
      </nav>
      <button className="site-navbar__toggle" type="button" aria-label={mobileOpen ? 'Close menu' : 'Open menu'} aria-expanded={mobileOpen} onClick={() => setMobileOpen((open) => !open)}>{mobileOpen ? <X size={21} /> : <Menu size={21} />}</button>
    </div>
  </header>;
}
