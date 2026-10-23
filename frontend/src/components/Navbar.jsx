import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import Logo from './Logo.jsx';
import './Navbar.css';

const primaryLinks = [
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Features', href: '#features' },
  { label: 'Risk Analytics', href: '#risk-analytics' },
  { label: 'About', href: '#about' },
];

export default function Navbar({ onLogin, authenticated = false }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeMenus = () => setMobileOpen(false);

  return <header className="site-navbar">
    <div className="site-navbar__inner">
      <Logo />
      <nav className={`site-navbar__links ${mobileOpen ? 'site-navbar__links--open' : ''}`} aria-label="Main navigation">
        {primaryLinks.map((item) => <a key={item.label} href={item.href} onClick={closeMenus}>{item.label}</a>)}
        <span className="site-navbar__divider" aria-hidden="true" />
        <div className="site-navbar__tools"><a className="site-navbar__explore clay-btn clay-btn--soft" href="#features" onClick={closeMenus}>Explore Features</a><button className="site-navbar__login clay-btn clay-btn--dark" type="button" onClick={() => { closeMenus(); onLogin(); }}>{authenticated ? 'Open workspace' : 'Login / Sign up'}</button></div>
      </nav>
      <button className="site-navbar__toggle" type="button" aria-label={mobileOpen ? 'Close menu' : 'Open menu'} aria-expanded={mobileOpen} onClick={() => setMobileOpen((open) => !open)}>{mobileOpen ? <X size={21} /> : <Menu size={21} />}</button>
    </div>
  </header>;
}
