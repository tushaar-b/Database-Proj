import { lazy, Suspense, useEffect, useState, useSyncExternalStore } from 'react';
import { useGSAP } from '@gsap/react';
import Navbar from './components/Navbar.jsx';
import MarketTicker from './components/MarketTicker.jsx';
import Hero from './components/Hero.jsx';
import IntroScroll from './components/IntroScroll/IntroScroll.jsx';
import { destroySmoothScroll, initSmoothScroll } from './lib/smoothScroll.js';
import WhyIntellivest from './components/WhyIntellivest.jsx';
import Products from './components/Products.jsx';
import RiskAnalytics from './components/SipCalculator.jsx';
import FinalCta from './components/FinalCta.jsx';
import Footer from './components/Footer.jsx';
import { authSession } from './api.js';
import './App.css';

const WorkspaceApp = lazy(() => import('./WorkspaceApp.jsx'));

function WorkspaceLoading() {
  return <main className="workspace-loading"><span className="workspace-loading__spinner" />Opening your IntelliVest workspace…</main>;
}

export default function App() {
  const session = useSyncExternalStore(authSession.subscribe, authSession.getSnapshot);
  const [showWorkspace, setShowWorkspace] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState('login');
  const openWorkspace = (mode) => { setWorkspaceMode(mode); setShowWorkspace(true); };
  const openHome = () => { setShowWorkspace(false); window.scrollTo({ top: 0, behavior: 'instant' }); };
  useEffect(() => { authSession.initialize().catch(() => {}); }, []);
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
  if (showWorkspace) return <Suspense fallback={<WorkspaceLoading />}><WorkspaceApp initialMode={workspaceMode} onHome={openHome} /></Suspense>;

  return <div className="landing-app" id="top">
    <Navbar authenticated={Boolean(session.user)} onLogin={() => openWorkspace('login')} />
    <IntroScroll />
    <Hero onGetStarted={() => openWorkspace('register')} />
    <MarketTicker />
    <div className="clay-divider" aria-hidden="true" />
    <WhyIntellivest />
    <div className="clay-divider clay-divider--lilac" aria-hidden="true" />
    <Products onGetStarted={() => openWorkspace('register')} />
    <div className="clay-divider clay-divider--peach" aria-hidden="true" />
    <RiskAnalytics />
    <div className="clay-divider" aria-hidden="true" />
    <FinalCta onGetStarted={() => openWorkspace('register')} />
    <Footer />
  </div>;
}
