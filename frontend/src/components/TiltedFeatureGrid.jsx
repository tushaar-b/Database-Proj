import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import './TiltedFeatureGrid.css';

const CAMERA = 1200;
const DECORATIVE_SLICES = 18;

// Positions share a cylinder: its front is z = 0 and its edges recede.
function arc(angle, radius) {
  const radians = angle * Math.PI / 180;
  return { x: Math.sin(radians) * radius, z: (Math.cos(radians) - 1) * radius };
}

function FinancialGraphic({ kind }) {
  return (
    <svg className="tilted-feature-grid__graphic" viewBox="0 0 280 70" fill="none" aria-hidden="true" focusable="false">
      {kind === 'lilac' ? <>
        <path d="M12 58H268" stroke="currentColor" opacity=".18" />
        {[26, 48, 34, 55, 42, 60, 48].map((height, index) => <rect key={index} x={24 + index * 34} y={64 - height} width="20" height={height - 6} rx="5" fill="currentColor" opacity={index === 5 ? '.45' : '.16'} />)}
      </> : kind === 'mint' ? <>
        <circle cx="140" cy="35" r="26" stroke="currentColor" strokeWidth="10" opacity=".12" />
        <circle cx="140" cy="35" r="26" stroke="currentColor" strokeWidth="10" strokeDasharray="63 164" transform="rotate(-90 140 35)" opacity=".45" />
        <path d="M32 24H88M32 44H74M192 24H248M206 44H248" stroke="currentColor" strokeWidth="7" strokeLinecap="round" opacity=".18" />
      </> : <>
        <path d="M16 18H264M16 36H264M16 54H264" stroke="currentColor" opacity=".1" />
        <path d="M20 52L64 40L108 47L152 20L196 31L260 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity=".5" />
        {[['64', '40'], ['152', '20'], ['196', '31']].map(([cx, cy]) => <circle key={cx} cx={cx} cy={cy} r="4" fill="currentColor" opacity=".5" />)}
      </>}
    </svg>
  );
}

export default function TiltedFeatureGrid({ features, onGetStarted }) {
  const [activeIndex, setActiveIndex] = useState(1);
  const root = useRef(null);
  const gesture = useRef(null);
  const suppressClickUntil = useRef(0);
  const count = features.length;
  const move = (direction) => setActiveIndex((index) => (index + direction + count) % count);

  useEffect(() => {
    const element = root.current;
    const measure = (width) => {
      const compact = width <= 600;
      const cardWidth = compact ? Math.max(0, width - 28) : Math.min(370, width * .46);
      const angle = compact ? 65 : width < 900 ? 26 : 32;
      const radius = compact ? cardWidth * 1.3 : Math.max(620, Math.min(790, width * .67));
      const { x, z } = arc(angle, radius);
      element.style.setProperty('--tilted-card-width', `${cardWidth}px`);
      element.style.setProperty('--tilted-side-x', `${x}px`);
      element.style.setProperty('--tilted-side-z', `${z}px`);
      element.style.setProperty('--tilted-side-angle', `${angle}deg`);
    };
    measure(element.getBoundingClientRect().width);
    const observer = new ResizeObserver(([entry]) => measure(entry.contentRect.width));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const selectLinkedFeature = () => {
      const index = features.findIndex(({ id }) => `#${id}` === window.location.hash);
      if (index !== -1) setActiveIndex(index);
    };
    selectLinkedFeature();
    window.addEventListener('hashchange', selectLinkedFeature);
    return () => window.removeEventListener('hashchange', selectLinkedFeature);
  }, [features]);

  const select = (index) => {
    setActiveIndex(index);
    root.current.focus({ preventScroll: true });
  };

  return (
    <div ref={root} className="tilted-feature-grid" style={{ '--tilted-camera': `${CAMERA}px` }}
      role="region" aria-roledescription="carousel" aria-label="Explore IntelliVest products" tabIndex={0}
      onKeyDown={(event) => {
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        event.preventDefault();
        move(event.key === 'ArrowLeft' ? -1 : 1);
        root.current.focus({ preventScroll: true });
      }}>
      <div className="tilted-feature-grid__viewport"
        onClickCapture={(event) => {
          if (Date.now() < suppressClickUntil.current) { event.preventDefault(); event.stopPropagation(); }
        }}
        onTouchStart={(event) => {
          gesture.current = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
        }}
        onTouchCancel={() => { gesture.current = null; }}
        onTouchEnd={(event) => {
          const start = gesture.current;
          gesture.current = null;
          if (!start || event.changedTouches.length !== 1) return;
          const dx = event.changedTouches[0].clientX - start.x;
          const dy = event.changedTouches[0].clientY - start.y;
          if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
            move(dx < 0 ? 1 : -1);
            suppressClickUntil.current = Date.now() + 450;
          }
        }}>
        <div className="tilted-feature-grid__decoration" aria-hidden="true">
          <div className="tilted-feature-grid__cylinder">
            {Array.from({ length: DECORATIVE_SLICES }, (_, index) => <span key={index} style={{ '--slice-angle': `${index * 360 / DECORATIVE_SLICES}deg` }} />)}
          </div>
        </div>
        <div className="tilted-feature-grid__stage">
          {features.map(({ id, name, icon: Icon, tint, copy, href, action }, index) => {
            const active = index === activeIndex;
            const position = active ? 'active' : index === (activeIndex - 1 + count) % count ? 'previous' : 'next';
            return (
              <article key={id} id={id} className={`tilted-feature-grid__card tilted-feature-grid__card--${tint} tilted-feature-grid__card--${position}`}
                role="group" aria-roledescription="slide" aria-label={`${index + 1} of ${count}: ${name}`}>
                <div className="tilted-feature-grid__meta"><span>{String(index + 1).padStart(2, '0')} <span>/ {String(count).padStart(2, '0')}</span></span><span>IntelliVest</span></div>
                <span className="tilted-feature-grid__icon"><Icon size={26} strokeWidth={1.7} aria-hidden="true" /></span>
                <FinancialGraphic kind={tint} />
                <h3>{name}</h3>
                <p>{copy}</p>
                <button type="button" className="tilted-feature-grid__select" aria-label={`Focus feature: ${name}`}
                  aria-hidden={active || undefined} tabIndex={active ? -1 : 0} onClick={() => select(index)} />
                {href ? <a className="tilted-feature-grid__cta" href={href}>{action}<ArrowRight size={16} aria-hidden="true" /></a>
                  : <button type="button" className="tilted-feature-grid__cta" onClick={onGetStarted}>{action}<ArrowRight size={16} aria-hidden="true" /></button>}
              </article>
            );
          })}
        </div>
      </div>
      <div className="tilted-feature-grid__controls" role="group" aria-label="Product navigation">
        <button type="button" className="tilted-feature-grid__arrow tilted-feature-grid__arrow--previous" aria-label="Previous product" onClick={() => move(-1)}><ArrowLeft size={20} strokeWidth={1.7} aria-hidden="true" /></button>
        <div className="tilted-feature-grid__pagination" role="group" aria-label="Choose a product">
          {features.map(({ id, name }, index) => <button key={id} type="button" aria-label={`Show feature ${index + 1}: ${name}`}
            aria-current={index === activeIndex ? 'true' : undefined} onClick={() => setActiveIndex(index)}><span /></button>)}
        </div>
        <button type="button" className="tilted-feature-grid__arrow tilted-feature-grid__arrow--next" aria-label="Next product" onClick={() => move(1)}><ArrowRight size={20} strokeWidth={1.7} aria-hidden="true" /></button>
      </div>
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">Feature {activeIndex + 1} of {count}: {features[activeIndex].name}</p>
    </div>
  );
}
