import { useId, useLayoutEffect, useRef } from 'react';
import { gsap } from 'gsap';
import '../IntroScroll/IntroScroll.css';
import './CinematicWelcome.css';

const WORDMARK = 'Intellivest';

// Preserve the original branded reveal, now following actual video completion.
export default function CinematicWelcome({ onComplete }) {
  const root = useRef(null);
  const gradientId = `cinematic-trend-${useId().replace(/:/g, '')}`;
  useLayoutEffect(() => {
    const element = root.current;
    const word = element.querySelector('.intro__word');
    const eyebrow = element.querySelector('.intro__eyebrow');
    const letters = [...element.querySelectorAll('.intro__letter')];
    const shimmer = element.querySelector('.intro__shimmer');
    const trend = element.querySelector('.intro__trend-path');
    const tagline = element.querySelector('.intro__tagline');
    const alignGradient = () => {
      const width = word.offsetWidth;
      letters.forEach(letter => {
        letter.style.setProperty('--word-width', `${width}px`);
        letter.style.setProperty('--letter-offset', `${letter.offsetLeft}px`);
      });
    };
    alignGradient();
    const observer = new ResizeObserver(alignGradient);
    observer.observe(word);
    const context = gsap.context(() => {
      const length = trend.getTotalLength();
      gsap.set(eyebrow, { y: 12, opacity: 0 });
      gsap.set(letters, { y: 60, opacity: 0, filter: 'blur(14px)', rotateX: -40 });
      gsap.set(tagline, { y: 16, opacity: 0 });
      gsap.set(trend, { strokeDasharray: length, strokeDashoffset: length });
      const lettersEnd = .12 + .8 + (WORDMARK.length - 1) * .06;
      gsap.timeline({ onComplete })
        .fromTo(element, { autoAlpha: 0 }, { autoAlpha: 1, duration: .4 }, 0)
        .to(eyebrow, { y: 0, opacity: 1, duration: .5 }, .1)
        .to(letters, { y: 0, opacity: 1, filter: 'blur(0px)', rotateX: 0, stagger: .06, duration: .8, ease: 'power4.out' }, .12)
        .set(shimmer, { opacity: 1 }, lettersEnd)
        .fromTo(shimmer, { backgroundPosition: '160% 0' }, { backgroundPosition: '-60% 0', duration: 1.1, ease: 'none' }, lettersEnd)
        .set(shimmer, { opacity: 0 }, lettersEnd + 1.1)
        .to(trend, { strokeDashoffset: 0, duration: .9, ease: 'power2.out' }, lettersEnd)
        .to(tagline, { y: 0, opacity: 1, duration: .5 }, lettersEnd + .2)
        .to({}, { duration: .45 });
    }, element);
    return () => { observer.disconnect(); context.revert(); };
  }, [onComplete]);

  return <div ref={root} className="intro__welcome cinematic-intro__welcome" role="status" aria-label="Welcome to Intellivest. Invest with intelligence.">
    <div className="intro__blobs" aria-hidden="true">{Array.from({ length: 7 }, (_, i) => <span key={i} />)}</div>
    <div className="intro__welcome-copy" aria-hidden="true">
      <p className="intro__eyebrow">WELCOME TO</p>
      <div className="intro__word-shell">
        <h2 className="intro__word">{[...WORDMARK].map((letter, index) => <span className="intro__letter" key={index}>{letter}</span>)}</h2>
        <span className="intro__shimmer">{WORDMARK}</span>
      </div>
      <svg className="intro__trend" width="128" height="48" viewBox="0 0 128 48" fill="none">
        <defs><linearGradient id={gradientId} x1="4" y1="36" x2="120" y2="8" gradientUnits="userSpaceOnUse"><stop stopColor="var(--indigo)" /><stop offset=".45" stopColor="var(--violet)" /><stop offset="1" stopColor="var(--coral)" /></linearGradient></defs>
        <path className="intro__trend-path" d="M4 38L31 24L49 31L76 16L93 23L120 7M104 7H120V22" stroke={`url(#${gradientId})`} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <p className="intro__tagline">Invest with intelligence.</p>
    </div>
  </div>;
}
