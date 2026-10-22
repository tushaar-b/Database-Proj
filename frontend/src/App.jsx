import { lazy, Suspense, useState } from 'react';
import { useGSAP } from '@gsap/react';
import Navbar from './components/Navbar.jsx';
import MarketTicker from './components/MarketTicker.jsx';
import Hero from './components/Hero.jsx';
import IntroScroll from './components/IntroScroll/IntroScroll.jsx';
import { destroySmoothScroll, initSmoothScroll } from './lib/smoothScroll.js';
import WhyIntellivest from './components/WhyIntellivest.jsx';
import Products from './components/Products.jsx';
import SipCalculator from './components/SipCalculator.jsx';
import FinalCta from './components/FinalCta.jsx';
import Footer from './components/Footer.jsx';
import './App.css';

const WorkspaceApp = lazy(() => import('./WorkspaceApp.jsx'));

function WorkspaceLoading() {
  return <main className="workspace-loading"><span className="workspace-loading__spinner" />Opening your IntelliVest workspace…</main>;
}

export default function App() {
  const [showWorkspace, setShowWorkspace] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState('login');
  const openWorkspace = (mode) => { setWorkspaceMode(mode); setShowWorkspace(true); };
  useGSAP(() => {
    if (showWorkspace) return undefined;
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const syncPreference = () => {
      if (preference.matches) destroySmoothScroll();
      else initSmoothScroll();
    };
    syncPreference();
    preference.addEventListener('change', syncPreference);
    return () => {
      preference.removeEventListener('change', syncPreference);
      destroySmoothScroll();
    };
  }, { dependencies: [showWorkspace], revertOnUpdate: true });
  if (showWorkspace) return <Suspense fallback={<WorkspaceLoading />}><WorkspaceApp initialMode={workspaceMode} /></Suspense>;

  return <div className="landing-app" id="top">
    <Navbar onLogin={() => openWorkspace('login')} />
    <IntroScroll />
    <Hero onGetStarted={() => openWorkspace('register')} />
    <MarketTicker />
    <div className="clay-divider" aria-hidden="true" />
    <WhyIntellivest />
    <div className="clay-divider clay-divider--lilac" aria-hidden="true" />
    <Products />
    <div className="clay-divider clay-divider--peach" aria-hidden="true" />
    <SipCalculator />
    <div className="clay-divider" aria-hidden="true" />
    <FinalCta onGetStarted={() => openWorkspace('register')} />
    <Footer />
  </div>;
}
