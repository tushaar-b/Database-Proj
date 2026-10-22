import { ArrowRight, CheckCircle2, Lock, MapPin } from 'lucide-react';
import ClayBlob from './ClayBlob.jsx';
import './Hero.css';

export default function Hero({ onGetStarted }) {
  return <main className="hero" id="hero">
    <ClayBlob tint="sun" className="hero__blob hero__blob--one" /><ClayBlob tint="coral" className="hero__blob hero__blob--two" /><ClayBlob tint="mint" className="hero__blob hero__blob--three" /><ClayBlob tint="lilac" className="hero__blob hero__blob--four" />
    <div className="hero__copy">
      <h1>Invest with <span>intelligence.</span></h1>
      <p className="hero__subtitle">Smarter research, simpler investing. Stocks, F&amp;O and Mutual Funds in one place.</p>
      <div className="hero__actions">
        <button className="hero__button clay-btn clay-btn--primary" type="button" onClick={onGetStarted}>Get started <ArrowRight size={16} /></button>
        <a className="hero__button clay-btn clay-btn--soft" href="#markets">Explore markets</a>
      </div>
      {/* Regulatory claims such as SEBI registration must be verified before launch. */}
      <div className="hero__trust" aria-label="Platform information">
        <span className="clay-chip"><CheckCircle2 size={14} />Zero account opening fee</span>
        <span className="clay-chip"><Lock size={14} />Secure by design</span>
        <span className="clay-chip"><MapPin size={14} />Built for Indian markets</span>
      </div>
    </div>
  </main>;
}
