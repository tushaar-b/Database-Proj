import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import './FeatureShowcase.css';

export default function FeatureShowcase({ features }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const touchStart = useRef(null);
  const count = features.length;
  const previousIndex = (activeIndex - 1 + count) % count;
  const nextIndex = (activeIndex + 1) % count;
  const move = (direction) => setActiveIndex((index) => (index + direction + count) % count);

  // Preserve existing footer feature links, including on initial load.
  useEffect(() => {
    const selectLinkedFeature = () => {
      const index = features.findIndex(({ id }) => `#${id}` === window.location.hash);
      if (index !== -1) setActiveIndex(index);
    };
    selectLinkedFeature();
    window.addEventListener('hashchange', selectLinkedFeature);
    return () => window.removeEventListener('hashchange', selectLinkedFeature);
  }, [features]);

  const handleKeyDown = (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    move(event.key === 'ArrowLeft' ? -1 : 1);
    // Retain keyboard focus when a card leaves the visible positions.
    event.currentTarget.focus({ preventScroll: true });
  };

  const handleTouchEnd = (event) => {
    const start = touchStart.current;
    touchStart.current = null;
    if (!start || event.changedTouches.length !== 1) return;
    const end = event.changedTouches[0];
    const dx = end.clientX - start.x;
    const dy = end.clientY - start.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) move(dx < 0 ? 1 : -1);
  };

  return (
    <div className="feature-showcase" role="region" aria-roledescription="carousel"
      aria-label="IntelliVest features" tabIndex={0} onKeyDown={handleKeyDown}>
      <div className="feature-showcase__viewport"
        onTouchStart={(event) => {
          touchStart.current = event.touches.length === 1
            ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
        }}
        onTouchEnd={handleTouchEnd} onTouchCancel={() => { touchStart.current = null; }}>
        {features.map(({ id, icon: Icon, title, copy, tint }, index) => {
          const position = index === activeIndex ? 'active'
            : index === previousIndex ? 'previous' : index === nextIndex ? 'next' : 'hidden';
          const active = position === 'active';
          const hidden = position === 'hidden';
          return (
            <article key={id} id={id} role="group" aria-roledescription="slide"
              aria-label={`${index + 1} of ${count}: ${title}`} aria-hidden={hidden || undefined}
              className={`feature-showcase__card feature-showcase__card--${tint} feature-showcase__card--${position}`}>
              <div className="feature-showcase__meta">
                <span className="feature-showcase__number">{String(index + 1).padStart(2, '0')} <span>/ {String(count).padStart(2, '0')}</span></span>
                <span className="feature-showcase__label" aria-hidden="true">IntelliVest feature</span>
              </div>
              <span className="feature-showcase__icon"><Icon size={26} strokeWidth={1.7} aria-hidden="true" /></span>
              <h3>{title}</h3>
              <p>{copy}</p>
              <button type="button" className="feature-showcase__select"
                tabIndex={hidden ? -1 : 0} aria-label={`Show feature ${index + 1}: ${title}`}
                aria-current={active ? 'true' : undefined} onClick={() => setActiveIndex(index)} />
            </article>
          );
        })}
      </div>
      <div className="feature-showcase__navigation" role="group" aria-label="Feature navigation">
        <button type="button" className="feature-showcase__arrow feature-showcase__arrow--previous"
          aria-label="Previous feature" onClick={() => move(-1)}><ArrowLeft size={20} strokeWidth={1.7} aria-hidden="true" /></button>
        <div className="feature-showcase__pagination" role="group" aria-label="Choose a feature">
          {features.map(({ id, title }, index) => (
            <button key={id} type="button" className="feature-showcase__indicator"
              aria-label={`Show feature ${index + 1}: ${title}`} aria-current={index === activeIndex ? 'true' : undefined}
              onClick={() => setActiveIndex(index)}><span /></button>
          ))}
        </div>
        <button type="button" className="feature-showcase__arrow feature-showcase__arrow--next"
          aria-label="Next feature" onClick={() => move(1)}><ArrowRight size={20} strokeWidth={1.7} aria-hidden="true" /></button>
      </div>
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        Feature {activeIndex + 1} of {count}: {features[activeIndex].title}
      </p>
    </div>
  );
}
