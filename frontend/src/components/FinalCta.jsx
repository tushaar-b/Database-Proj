import { ArrowRight } from 'lucide-react';
import useSectionReveal from '../hooks/useSectionReveal.js';
import ClayBlob from './ClayBlob.jsx';
import './FinalCta.css';
export default function FinalCta({ onGetStarted }) {
  const scope = useSectionReveal();
  return <section className="final-cta" id="get-started" ref={scope}><div className="final-cta__card clay-card clay-card--sun" data-clay-reveal><ClayBlob tint="coral" className="final-cta__blob" /><span className="clay-badge">A brighter perspective</span><h2>Ready to understand your investments better?</h2><p>Start with your financial picture. Understand your portfolio. Explore investing with greater clarity.</p><button type="button" className="clay-btn clay-btn--primary" onClick={onGetStarted}>Get started <ArrowRight size={16} /></button></div></section>;
}
