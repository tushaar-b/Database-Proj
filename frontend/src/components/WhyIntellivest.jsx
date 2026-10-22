import { BookOpen, Sprout, Layers3, MapPin } from 'lucide-react';
import useSectionReveal from '../hooks/useSectionReveal.js';
import ClayBlob from './ClayBlob.jsx';
import './WhyIntellivest.css';

const reasons = [
  { icon: BookOpen, title: 'Research that explains itself', copy: 'Bring the reasons behind an investing idea into focus.', tint: 'lilac' },
  { icon: Sprout, title: 'Start a SIP in minutes', copy: 'Explore a regular investing habit with our illustrative SIP planner.', tint: 'mint' },
  { icon: Layers3, title: 'F&O, clearly laid out', copy: 'Make sense of derivatives and the risks that come with them.', tint: 'coral' },
  { icon: MapPin, title: 'Built for Indian markets', copy: 'Keep Indian market context at the heart of your research.', tint: 'sun' },
];
export default function WhyIntellivest() {
  const scope = useSectionReveal();
  return <section className="why" id="features" ref={scope} aria-labelledby="why-title">
    <ClayBlob tint="mint" className="why__blob" />
    <div className="why__inner">
      <div className="why__heading" data-clay-reveal><span className="clay-badge">A little more perspective</span><h2 id="why-title">Why Intellivest</h2><p>A thoughtful place to explore what investing could look like for you.</p></div>
      <div className="why__grid">{reasons.map(({ icon: Icon, title, copy, tint }) => <article className={`why__card clay-card clay-card--${tint}`} key={title} data-clay-reveal><span className="why__icon"><Icon size={23} aria-hidden="true" /></span><h3>{title}</h3><p>{copy}</p></article>)}</div>
    </div>
  </section>;
}
