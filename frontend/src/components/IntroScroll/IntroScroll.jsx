import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { getLenis } from '../../lib/smoothScroll.js';
import useReducedMotion from '../../hooks/useReducedMotion.js';
import './IntroScroll.css';

// Timing, image quality, and doorway bloom controls live together here.
const FRAMES_END = 0.86;
const FLASH_START = 0.78;
const FLASH_FULL = 0.88;
const WELCOME_AT = 0.90;
// Hold just beyond the threshold so pixel rounding cannot reverse the welcome.
const WELCOME_HOLD_PROGRESS = WELCOME_AT + 0.002;
const SCROLL_KEYS = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'PageUp', 'PageDown', 'Home', 'End', ' ', 'Spacebar']);
// Crisp source frames take priority over crossfade smoothing and extra zoom.
const BLEND_FRAMES = false;
const DPR_CAP = 3;
const MAX_CANVAS_PIXELS = 3840 * 2160;
const EXTRA_PUSH = 0;
const BLEND_MINIMUM = 0.02;
const EXPECTED_FRAME_COUNT = 120;
const PRIORITY_FRAME_COUNT = 15;
const LOAD_BATCH_SIZE = 10;
const LOADER_TIMEOUT_MS = 8000;
const LOADER_FADE_MS = 500;
const RESIZE_DEBOUNCE_MS = 150;
const DESKTOP_DISTANCE = '+=500%';
const MOBILE_DISTANCE = '+=380%';
const MOBILE_QUERY = '(max-width: 768px)';
const DESKTOP_QUERY = '(min-width: 769px)';
const SCRUB_DURATION = 0.6;
const FLASH_X = '50%';
const FLASH_Y = '72%';
const BLOOM_START_SCALE = 0.4;
const BLOOM_END_SCALE = 2.2;
const WHITEOUT_START = FLASH_START + (FLASH_FULL - FLASH_START) * 0.5;
const HERO_FADE_DURATION = 0.24;
const WORDMARK = 'Intellivest';
const WELCOME_TIMING = {
  eyebrow: 0.5,
  lettersStart: 0.12,
  letters: 0.8,
  stagger: 0.06,
  shimmer: 1.1,
  line: 0.9,
  tagline: 0.5,
};

// Vite's root is frontend/. These importer-relative globs reach the existing
// project-root video directory without moving assets or using public URLs.
const hqModules = import.meta.glob('../../../../video/frames/*.jpg', {
  eager: true, query: '?url', import: 'default',
});
const smModules = import.meta.glob('../../../../video/frames-sm/*.jpg', {
  eager: true, query: '?url', import: 'default',
});
const toList = (modules) => Object.keys(modules).sort().map((key) => modules[key]);
const hqList = toList(hqModules);
const smList = toList(smModules);
const connection = typeof navigator !== 'undefined' ? navigator.connection : undefined;
// Use the 1080p originals on mobile too; reserve 720p for constrained networks.
const useSmall = (
  connection?.saveData === true
  || ['slow-2g', '2g', '3g'].includes(connection?.effectiveType)
);
const FRAME_URLS = useSmall
  ? (smList.length ? smList : hqList)
  : (hqList.length ? hqList : smList);
const FRAME_COUNT = FRAME_URLS.length;
if (FRAME_COUNT !== EXPECTED_FRAME_COUNT) {
  console.warn(`Intellivest intro: expected ${EXPECTED_FRAME_COUNT} frames, found ${FRAME_COUNT}.`);
}

export default function IntroScroll() {
  const sectionRef = useRef(null);
  const canvasRef = useRef(null);
  const reducedMotion = useReducedMotion();
  const [percent, setPercent] = useState(0);
  const [ready, setReady] = useState(reducedMotion || FRAME_COUNT === 0);
  const [showLoader, setShowLoader] = useState(!reducedMotion && FRAME_COUNT > 0);
  const gradientId = `intro-trend-${useId().replace(/:/g, '')}`;

  // Hide the navbar before the first paint, without changing its component.
  useLayoutEffect(() => {
    const html = document.documentElement;
    const previous = html.getAttribute('data-intro');
    html.dataset.intro = reducedMotion ? 'done' : 'active';
    return () => {
      if (previous === null) delete html.dataset.intro;
      else html.setAttribute('data-intro', previous);
    };
  }, [reducedMotion]);

  useEffect(() => {
    const section = sectionRef.current;
    const canvas = canvasRef.current;
    const context2d = canvas.getContext('2d', { alpha: false });
    const html = document.documentElement;
    const images = new Array(FRAME_COUNT);
    const pendingLoads = new Set();
    const model = { frame: reducedMotion ? Math.max(0, FRAME_COUNT - 1) : 0, progress: reducedMotion ? 1 : 0 };
    let disposed = false;
    let settled = 0;
    let finishedLoading = reducedMotion || FRAME_COUNT === 0;
    let drawRaf = 0;
    let refreshRaf = 0;
    let resizeTimer = 0;
    let loaderTimer = 0;
    let fadeTimer = 0;
    let forcedDraw = false;
    let lastFrame = NaN;
    let lastProgress = NaN;
    const scrollLocks = new Set();
    let lockedPosition = null;
    let lockStyles = [];
    let lenisWasStopped = false;
    const welcome = section.querySelector('.intro__welcome');
    const eyebrow = section.querySelector('.intro__eyebrow');
    const word = section.querySelector('.intro__word');
    const letters = section.querySelectorAll('.intro__letter');
    const shimmer = section.querySelector('.intro__shimmer');
    const trendPath = section.querySelector('.intro__trend-path');
    const tagline = section.querySelector('.intro__tagline');
    const flash = section.querySelector('.intro__flash');
    const bloom = section.querySelector('.intro__bloom');
    const whiteout = section.querySelector('.intro__whiteout');
    const progressBar = section.querySelector('.intro__progress');

    setPercent(0);
    setReady(finishedLoading);
    setShowLoader(!finishedLoading);

    function blockScrollInput(event) {
      if (!scrollLocks.size || event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.type === 'touchmove' && event.touches.length > 1) return;
      if (event.type === 'keydown') {
        if (!SCROLL_KEYS.has(event.key)) return;
        if (event.target instanceof Element && event.target.closest('input, textarea, select, [contenteditable="true"]')) return;
      }
      if (event.cancelable) event.preventDefault();
    }

    function restoreLockedPosition() {
      if (!scrollLocks.size || !lockedPosition) return;
      if (Math.abs(window.scrollY - lockedPosition.y) > 0.5 || Math.abs(window.scrollX - lockedPosition.x) > 0.5) {
        window.scrollTo({ top: lockedPosition.y, left: lockedPosition.x, behavior: 'instant' });
      }
    }

    // Loading and the welcome own separate locks, so finishing an image batch
    // cannot accidentally release an in-progress welcome animation.
    function acquireScroll(reason, anchor = window.scrollY) {
      if (scrollLocks.has(reason)) return;
      const firstLock = scrollLocks.size === 0;
      scrollLocks.add(reason);
      lockedPosition = { x: window.scrollX, y: anchor };
      if (firstLock) {
        lockStyles = [
          [html.style, 'overflow'], [html.style, 'scrollbar-gutter'],
          [html.style, 'overscroll-behavior'], [document.body.style, 'overflow'],
          [document.body.style, 'overscroll-behavior'],
        ].map(([style, property]) => ({ style, property, value: style.getPropertyValue(property), priority: style.getPropertyPriority(property) }));
        const lenis = getLenis();
        lenisWasStopped = lenis?.isStopped ?? false;
        lenis?.stop();
        html.style.setProperty('scrollbar-gutter', 'stable');
        html.style.overflow = 'hidden';
        html.style.overscrollBehavior = 'none';
        document.body.style.overflow = 'hidden';
        document.body.style.overscrollBehavior = 'none';
        window.addEventListener('wheel', blockScrollInput, { passive: false, capture: true });
        window.addEventListener('touchmove', blockScrollInput, { passive: false, capture: true });
        window.addEventListener('keydown', blockScrollInput, true);
        window.addEventListener('scroll', restoreLockedPosition, { passive: true, capture: true });
      }
      const lenis = getLenis();
      if (lenis) lenis.scrollTo(anchor, { immediate: true, force: true });
      else restoreLockedPosition();
    }

    function releaseScroll(reason) {
      if (reason) scrollLocks.delete(reason);
      else scrollLocks.clear();
      if (scrollLocks.size || !lockedPosition) return;
      lockedPosition = null;
      window.removeEventListener('wheel', blockScrollInput, true);
      window.removeEventListener('touchmove', blockScrollInput, true);
      window.removeEventListener('keydown', blockScrollInput, true);
      window.removeEventListener('scroll', restoreLockedPosition, true);
      lockStyles.forEach(({ style, property, value, priority }) => {
        if (value) style.setProperty(property, value, priority);
        else style.removeProperty(property);
      });
      lockStyles = [];
      if (!lenisWasStopped) getLenis()?.start();
    }

    if (!finishedLoading) acquireScroll('loading');

    // Resolve an unavailable frame to the nearest earlier usable frame.
    function availableFrame(index) {
      for (let i = Math.min(index, FRAME_COUNT - 1); i >= 0; i -= 1) {
        if (images[i]?.naturalWidth) return images[i];
      }
      return images.find((image) => image?.naturalWidth) || null;
    }

    function publishFrame(index, image) {
      const floor = Math.floor(model.frame);
      const current = availableFrame(floor);
      const next = availableFrame(floor + 1);
      images[index] = image;
      const blending = BLEND_FRAMES && model.frame - floor >= BLEND_MINIMUM;
      if (current !== availableFrame(floor) || (blending && next !== availableFrame(floor + 1))) {
        requestDraw(true);
      }
    }

    function drawCover(image) {
      const scale = Math.max(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight)
        * (1 + EXTRA_PUSH * model.progress);
      const width = Math.round(image.naturalWidth * scale);
      const height = Math.round(image.naturalHeight * scale);
      const x = Math.round((canvas.width - width) / 2);
      const y = Math.round((canvas.height - height) / 2);
      context2d.drawImage(image, x, y, width, height);
    }

    function draw(force = false) {
      if (disposed || !context2d) return;
      if (!force && model.frame === lastFrame && model.progress === lastProgress) return;
      context2d.imageSmoothingEnabled = true;
      context2d.imageSmoothingQuality = 'high';
      context2d.globalAlpha = 1;
      context2d.fillStyle = getComputedStyle(html).getPropertyValue('--flash-color').trim();
      context2d.fillRect(0, 0, canvas.width, canvas.height);
      const position = Math.max(0, Math.min(FRAME_COUNT - 1, model.frame));
      const floor = Math.floor(position);
      const fraction = position - floor;
      const current = availableFrame(floor);
      if (current) drawCover(current);
      if (BLEND_FRAMES && fraction >= BLEND_MINIMUM && floor < FRAME_COUNT - 1) {
        const next = availableFrame(floor + 1);
        if (next && next !== current) {
          context2d.globalAlpha = fraction;
          drawCover(next);
        }
      }
      context2d.globalAlpha = 1;
      lastFrame = model.frame;
      lastProgress = model.progress;
    }

    // Scroll callbacks only request a draw; multiple updates share one RAF.
    function requestDraw(force = false) {
      if (disposed) return;
      forcedDraw ||= force;
      if (drawRaf || (!forcedDraw && model.frame === lastFrame && model.progress === lastProgress)) return;
      drawRaf = window.requestAnimationFrame(() => {
        drawRaf = 0;
        draw(forcedDraw);
        forcedDraw = false;
      });
    }

    function alignWordGradient() {
      const width = word.getBoundingClientRect().width;
      letters.forEach((letter) => {
        letter.style.setProperty('--word-width', `${width}px`);
        letter.style.setProperty('--letter-offset', `${letter.offsetLeft}px`);
      });
    }

    function resizeCanvas() {
      if (disposed) return;
      const { width, height } = section.getBoundingClientRect();
      // Render directly at display density without CSS upscaling. Bound the
      // backing store to a 4K pixel budget on large or high-density screens.
      const budgetDpr = Math.sqrt(MAX_CANVAS_PIXELS / Math.max(1, width * height));
      const dpr = Math.min(window.devicePixelRatio || 1, DPR_CAP, budgetDpr);
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      alignWordGradient();
      requestDraw(true);
    }

    function finishLoading() {
      if (disposed || finishedLoading) return;
      finishedLoading = true;
      window.clearTimeout(loaderTimer);
      setReady(true);
      releaseScroll('loading');
      fadeTimer = window.setTimeout(() => { if (!disposed) setShowLoader(false); }, LOADER_FADE_MS);
      refreshRaf = window.requestAnimationFrame(() => {
        refreshRaf = 0;
        getLenis()?.resize();
        ScrollTrigger.refresh();
        resizeCanvas();
      });
    }

    async function loadFrame(index) {
      if (disposed) return;
      await new Promise((resolve) => {
        const image = new Image();
        image.decoding = 'async';
        image.fetchPriority = index < PRIORITY_FRAME_COUNT ? 'high' : 'low';
        let completed = false;
        const cancel = () => settle(false);
        function settle(success) {
          if (completed) return;
          completed = true;
          image.onload = null;
          image.onerror = null;
          pendingLoads.delete(cancel);
          if (!disposed) {
            publishFrame(index, success ? image : availableFrame(index - 1));
            settled += 1;
            setPercent(Math.round(settled / FRAME_COUNT * 100));
            if (settled === FRAME_COUNT) finishLoading();
          }
          resolve();
        }
        pendingLoads.add(cancel);
        image.onload = () => {
          if (disposed) { settle(false); return; }
          if (index === 0 || (reducedMotion && index === FRAME_COUNT - 1)) {
            publishFrame(index, image);
          }
          image.decode().catch(() => {}).then(() => settle(image.naturalWidth > 0));
        };
        image.onerror = () => settle(false);
        image.src = FRAME_URLS[index];
      });
    }

    // The microtask prevents StrictMode's discarded first effect from loading
    // a duplicate sequence. Reduced motion needs only the final still image.
    Promise.resolve().then(async () => {
      if (disposed || !FRAME_COUNT) return;
      if (reducedMotion) {
        await loadFrame(FRAME_COUNT - 1);
        if (!disposed) setPercent(100);
        return;
      }
      const firstBatch = Math.min(PRIORITY_FRAME_COUNT, FRAME_COUNT);
      await Promise.all(Array.from({ length: firstBatch }, (_, index) => loadFrame(index)));
      for (let start = firstBatch; start < FRAME_COUNT && !disposed; start += LOAD_BATCH_SIZE) {
        const count = Math.min(LOAD_BATCH_SIZE, FRAME_COUNT - start);
        await Promise.all(Array.from({ length: count }, (_, offset) => loadFrame(start + offset)));
      }
      finishLoading();
    });

    const media = gsap.matchMedia();
    const animations = gsap.context(() => {
      media.add({ desktop: DESKTOP_QUERY, mobile: MOBILE_QUERY }, ({ conditions }) => {
        const lineLength = trendPath.getTotalLength();
        if (reducedMotion || !FRAME_COUNT) {
          gsap.set(welcome, { autoAlpha: 1 });
          gsap.set([eyebrow, ...letters, tagline], { opacity: 1, y: 0, rotateX: 0, filter: 'blur(0px)' });
          gsap.set(trendPath, { strokeDasharray: lineLength, strokeDashoffset: 0 });
          gsap.set(flash, { opacity: 1 });
          gsap.set(whiteout, { opacity: 0.85 });
          gsap.set([bloom, shimmer, progressBar], { opacity: 0 });
          html.dataset.intro = 'done';
          requestDraw(true);
          return undefined;
        }

        gsap.set(eyebrow, { y: 12, opacity: 0 });
        gsap.set(letters, { y: 60, opacity: 0, filter: 'blur(14px)', rotateX: -40 });
        gsap.set(tagline, { y: 16, opacity: 0 });
        gsap.set(trendPath, { strokeDasharray: lineLength, strokeDashoffset: lineLength });
        const lettersEnd = WELCOME_TIMING.lettersStart + WELCOME_TIMING.letters
          + (WORDMARK.length - 1) * WELCOME_TIMING.stagger;
        let welcomeShown = false;
        let welcomeHolding = false;
        let active = true;
        let masterReady = false;
        let master;
        function releaseWelcome() {
          welcomeHolding = false;
          releaseScroll('welcome');
        }
        const welcomeTimeline = gsap.timeline({
          paused: true,
          onComplete: releaseWelcome,
          onInterrupt: () => {
            active = false;
            releaseWelcome();
          },
        })
          .fromTo(welcome, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.01 }, 0)
          .to(eyebrow, { y: 0, opacity: 1, duration: WELCOME_TIMING.eyebrow }, 0)
          .to(letters, { y: 0, opacity: 1, filter: 'blur(0px)', rotateX: 0, stagger: WELCOME_TIMING.stagger, duration: WELCOME_TIMING.letters, ease: 'power4.out' }, WELCOME_TIMING.lettersStart)
          .set(shimmer, { opacity: 1 }, lettersEnd)
          .fromTo(shimmer, { backgroundPosition: '160% 0' }, { backgroundPosition: '-60% 0', duration: WELCOME_TIMING.shimmer, ease: 'none' }, lettersEnd)
          .set(shimmer, { opacity: 0 }, lettersEnd + WELCOME_TIMING.shimmer)
          .to(trendPath, { strokeDashoffset: 0, duration: WELCOME_TIMING.line, ease: 'power2.out' }, lettersEnd)
          .to(tagline, { y: 0, opacity: 1, duration: WELCOME_TIMING.tagline }, lettersEnd + 0.2);

        function update(progress, fromScroll = false) {
          if (disposed || !active || !masterReady) return;
          // Use the scrubbed playhead so welcome never precedes the whiteout.
          const visualProgress = master ? master.progress() : progress;
          requestDraw();
          const reachedWelcome = (fromScroll ? progress : visualProgress) >= WELCOME_AT;
          if (finishedLoading && reachedWelcome && !welcomeShown) {
            welcomeShown = true;
            welcomeHolding = true;
            const trigger = master?.scrollTrigger;
            if (trigger) {
              // Clamp fast swipes and wheel momentum back inside the pin before
              // playing the non-scrubbed welcome, then freeze all scroll input.
              const anchor = Math.ceil(trigger.start + (trigger.end - trigger.start) * WELCOME_HOLD_PROGRESS);
              acquireScroll('welcome', anchor);
              master.progress(WELCOME_HOLD_PROGRESS);
            } else acquireScroll('welcome');
            welcomeTimeline.play();
          } else if (!welcomeHolding && visualProgress < WELCOME_AT && welcomeShown) {
            welcomeShown = false;
            welcomeTimeline.reverse();
          }
          const beforeEnd = !master?.scrollTrigger || window.scrollY <= master.scrollTrigger.end;
          html.dataset.intro = !welcomeHolding && beforeEnd && visualProgress < WELCOME_AT ? 'active' : 'done';
        }

        master = gsap.timeline({
          onUpdate: () => update(master?.progress() || 0),
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: conditions.mobile ? MOBILE_DISTANCE : DESKTOP_DISTANCE,
            pin: true,
            pinSpacing: true,
            scrub: SCRUB_DURATION,
            anticipatePin: 1,
            onUpdate: (self) => update(self.progress, true),
            onToggle: (self) => update(self.progress, true),
          },
        });
        master
          .fromTo(model, { progress: 0 }, { progress: 1, duration: 1, ease: 'none' }, 0)
          .fromTo(model, { frame: 0 }, { frame: FRAME_COUNT - 1, duration: FRAMES_END, ease: 'none', onUpdate: () => requestDraw() }, 0)
          .fromTo(flash, { opacity: 0 }, { opacity: 1, duration: FLASH_FULL - FLASH_START, ease: 'power2.in' }, FLASH_START)
          .fromTo(bloom, { scale: BLOOM_START_SCALE }, { scale: BLOOM_END_SCALE, duration: FLASH_FULL - FLASH_START, ease: 'power2.in' }, FLASH_START)
          .fromTo(whiteout, { opacity: 0 }, { opacity: 1, duration: FLASH_FULL - WHITEOUT_START, ease: 'power2.in' }, WHITEOUT_START)
          .fromTo(progressBar, { scaleX: 0 }, { scaleX: 1, duration: 1, ease: 'none' }, 0)
          .fromTo(progressBar, { opacity: 1 }, { opacity: 0, duration: FLASH_FULL - FLASH_START, ease: 'none' }, FLASH_START);

        const hero = document.getElementById('hero');
        const heroCopy = hero?.querySelector('.hero__copy');
        if (heroCopy) gsap.from(heroCopy, {
          y: 18, autoAlpha: 0, duration: HERO_FADE_DURATION, ease: 'power2.out',
          scrollTrigger: { trigger: hero, start: 'top 88%', toggleActions: 'play none none reverse' },
        });
        masterReady = true;
        update(master.progress());
        return () => {
          active = false;
          releaseWelcome();
        };
      });
    }, section);

    function onResize() {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => {
        ScrollTrigger.refresh();
        resizeCanvas();
      }, RESIZE_DEBOUNCE_MS);
    }
    window.addEventListener('resize', onResize, { passive: true });
    ScrollTrigger.addEventListener('refresh', resizeCanvas);
    resizeCanvas();
    if (!finishedLoading) loaderTimer = window.setTimeout(finishLoading, LOADER_TIMEOUT_MS);
    document.fonts?.ready.then(() => { if (!disposed) alignWordGradient(); });

    return () => {
      disposed = true;
      window.removeEventListener('resize', onResize);
      ScrollTrigger.removeEventListener('refresh', resizeCanvas);
      window.clearTimeout(resizeTimer);
      window.clearTimeout(loaderTimer);
      window.clearTimeout(fadeTimer);
      window.cancelAnimationFrame(drawRaf);
      window.cancelAnimationFrame(refreshRaf);
      pendingLoads.forEach((cancel) => cancel());
      media.revert();
      animations.revert();
      releaseScroll();
    };
  }, [reducedMotion]);

  return <section ref={sectionRef} className="intro" id="intro" aria-busy={!ready}
    style={{ '--flash-x': FLASH_X, '--flash-y': FLASH_Y, '--intro-loader-fade': `${LOADER_FADE_MS}ms` }}>
    <canvas ref={canvasRef} className="intro__canvas" role="img"
      aria-label="Animated clay-style city camera moving into the Intellivest stock exchange building" />
    <div className="intro__flash" aria-hidden="true"><div className="intro__bloom" /><div className="intro__whiteout" /></div>
    <div className="intro__progress" aria-hidden="true" />
    <div className="intro__welcome">
      <div className="intro__blobs" aria-hidden="true">{Array.from({ length: 7 }, (_, i) => <span key={i} />)}</div>
      <div className="intro__welcome-copy">
        <p className="intro__eyebrow">WELCOME TO</p>
        <div className="intro__word-shell">
          <h2 className="intro__word" aria-label={WORDMARK}>{[...WORDMARK].map((letter, index) => <span className="intro__letter" key={index} aria-hidden="true">{letter}</span>)}</h2>
          <span className="intro__shimmer" aria-hidden="true">{WORDMARK}</span>
        </div>
        <svg className="intro__trend" width="128" height="48" viewBox="0 0 128 48" fill="none" aria-hidden="true">
          <defs><linearGradient id={gradientId} x1="4" y1="36" x2="120" y2="8" gradientUnits="userSpaceOnUse"><stop stopColor="var(--indigo)" /><stop offset=".45" stopColor="var(--violet)" /><stop offset="1" stopColor="var(--coral)" /></linearGradient></defs>
          <path className="intro__trend-path" d="M4 38L31 24L49 31L76 16L93 23L120 7M104 7H120V22" stroke={`url(#${gradientId})`} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p className="intro__tagline">Invest with intelligence.</p>
      </div>
    </div>
    {showLoader && <div className={`intro__loader${ready ? ' intro__loader--ready' : ''}`} role="status" aria-live="polite" aria-hidden={ready}>
      <span className="intro__loader-ring" aria-hidden="true" style={{ '--load-progress': `${percent}%` }} />
      <span className="intro__loader-label">Preparing your journey <strong>{percent}%</strong></span>
    </div>}
  </section>;
}
