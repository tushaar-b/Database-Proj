import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

// Shares the application's ScrollTrigger/Lenis setup; never creates another scroller.
export default function useSectionReveal() {
  const scope = useRef(null);
  useGSAP(() => {
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const section = scope.current;
      if (!section) return;
      gsap.from(section.querySelectorAll('[data-clay-reveal]'), {
        y: 28, opacity: 0, duration: .6, stagger: .08, ease: 'power2.out',
        scrollTrigger: { trigger: section, start: 'top 88%', once: true },
      });
      section.querySelectorAll('.clay-blob').forEach((blob) => gsap.to(blob, {
        y: -18, ease: 'none', scrollTrigger: { trigger: section, start: 'top bottom', end: 'bottom top', scrub: true },
      }));
    });
    return () => media.revert();
  }, { scope });
  return scope;
}
