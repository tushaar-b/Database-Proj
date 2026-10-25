import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import CinematicShinyButton from '../CinematicShinyButton.jsx';
import CinematicWelcome from './CinematicWelcome.jsx';
import useReducedMotion from '../../hooks/useReducedMotion.js';
import cityVideo from '../../../../video/Camera_pushing_into_clay_building_20261022012746.mp4?url';
import cityPoster from '../../../../video/frames/frame_001.jpg?url';
import './CinematicIntro.css';

// Original 10-second scene at a faster cinematic pace. Keep timing in one place.
const PLAYBACK_RATE = 3.0;
const TRANSITION_MS = 760;
const MEDIA_WAIT_MS = 15000;

export default function CinematicIntro({ onReveal, onComplete }) {
  const dialogRef = useRef(null);
  const videoRef = useRef(null);
  const buttonRef = useRef(null);
  const mounted = useRef(false);
  const phaseRef = useRef('ready');
  const requestId = useRef(0);
  const finishTimer = useRef(null);
  const mediaTimer = useRef(null);
  const completed = useRef(false);
  const [phase, setPhase] = useState('ready');
  const [ready, setReady] = useState(false);
  const [buffering, setBuffering] = useState(false);
  const [error, setError] = useState('');
  const [assetFailed, setAssetFailed] = useState(false);
  const reducedMotion = useReducedMotion();
  const titleId = useId();
  const descriptionId = useId();
  const statusId = useId();

  const changePhase = useCallback(next => { phaseRef.current = next; setPhase(next); }, []);
  const skip = useCallback(() => {
    if (completed.current) return;
    completed.current = true;
    requestId.current += 1;
    clearTimeout(finishTimer.current);
    clearTimeout(mediaTimer.current);
    videoRef.current?.pause();
    onComplete();
  }, [onComplete]);

  useLayoutEffect(() => {
    const dialog = dialogRef.current;
    const video = videoRef.current;
    const htmlOverflow = document.documentElement.style.overflow;
    const bodyOverflow = document.body.style.overflow;
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    dialog.showModal();
    buttonRef.current = dialog.querySelector('.cinematic-shiny-button');
    buttonRef.current?.focus({ preventScroll: true });
    return () => {
      video?.pause();
      dialog.close();
      document.documentElement.style.overflow = htmlOverflow;
      document.body.style.overflow = bodyOverflow;
    };
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      requestId.current += 1;
      clearTimeout(finishTimer.current);
      clearTimeout(mediaTimer.current);
    };
  }, []);

  const recover = useCallback(message => {
    if (!mounted.current || completed.current || ['welcome', 'finishing'].includes(phaseRef.current)) return;
    requestId.current += 1;
    clearTimeout(mediaTimer.current);
    videoRef.current?.pause();
    setBuffering(false);
    setError(message);
    changePhase('failed');
    requestAnimationFrame(() => {
      if (mounted.current && !completed.current) buttonRef.current?.focus({ preventScroll: true });
    });
  }, [changePhase]);

  const armPlaybackTimeout = useCallback(() => {
    clearTimeout(mediaTimer.current);
    mediaTimer.current = setTimeout(() => recover('The animation is taking too long to play. Try again or enter the website below.'), MEDIA_WAIT_MS);
  }, [recover]);

  useEffect(() => {
    if (reducedMotion && ['starting', 'playing', 'welcome', 'finishing'].includes(phaseRef.current)) skip();
  }, [reducedMotion, skip]);

  useEffect(() => {
    if (ready || reducedMotion) return undefined;
    const timer = setTimeout(() => {
      if (phaseRef.current === 'ready') setError('The scene is still loading. You can try playback or enter the website directly.');
    }, MEDIA_WAIT_MS);
    return () => clearTimeout(timer);
  }, [ready, reducedMotion]);

  function start() {
    if (completed.current || !['ready', 'failed'].includes(phaseRef.current)) return;
    if (reducedMotion) { skip(); return; }
    const video = videoRef.current;
    if (!video) { recover('The animation is unavailable. Enter the website directly below.'); return; }
    const ticket = ++requestId.current;
    setError('');
    setAssetFailed(false);
    setBuffering(true);
    changePhase('starting');
    // play() is called synchronously inside the actual user gesture. There is
    // no autoplay, scroll scrub, deferred click or dependency on audio permission.
    video.muted = true;
    video.playbackRate = PLAYBACK_RATE;
    if (video.error) video.load();
    armPlaybackTimeout();
    try {
      const playback = video.play();
      playback?.catch(() => {
        if (ticket === requestId.current) recover('Playback could not start. Try the button again, or enter the website directly below.');
      });
    } catch {
      recover('Playback could not start. Try again or enter the website directly below.');
    }
  }

  function playing() {
    if (completed.current || !['starting', 'playing'].includes(phaseRef.current)) {
      videoRef.current?.pause();
      return;
    }
    clearTimeout(mediaTimer.current);
    setReady(true);
    setBuffering(false);
    changePhase('playing');
  }

  const finish = useCallback(() => {
    if (completed.current || phaseRef.current === 'finishing') return;
    if (reducedMotion) { skip(); return; }
    requestId.current += 1;
    clearTimeout(mediaTimer.current);
    setBuffering(false);
    changePhase('finishing');
    onReveal();
    finishTimer.current = setTimeout(skip, TRANSITION_MS);
  }, [reducedMotion, skip, changePhase, onReveal]);

  function beginWelcome() {
    if (completed.current || !['starting', 'playing'].includes(phaseRef.current)) return;
    requestId.current += 1;
    clearTimeout(mediaTimer.current);
    setBuffering(false);
    setError('');
    changePhase('welcome');
  }

  const busy = ['starting', 'playing', 'welcome', 'finishing'].includes(phase);
  return <dialog ref={dialogRef} className={`cinematic-intro cinematic-intro--${phase}`} aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId}
    style={{ '--cinematic-fade-duration': `${TRANSITION_MS}ms`, backgroundImage: `url("${cityPoster}")` }}
    onCancel={event => { event.preventDefault(); skip(); }}>
    <video ref={videoRef} className={`cinematic-intro__video${assetFailed ? ' cinematic-intro__video--unavailable' : ''}`} src={cityVideo} poster={cityPoster}
      muted playsInline preload={reducedMotion ? 'none' : 'auto'} aria-hidden="true" tabIndex={-1}
      onLoadedData={() => { setReady(true); if (phaseRef.current === 'ready') setError(''); }}
      onCanPlay={() => { setReady(true); if (phaseRef.current === 'ready') setError(''); }}
      onPlaying={playing} onEnded={beginWelcome}
      onWaiting={() => { if (['starting', 'playing'].includes(phaseRef.current)) { setBuffering(true); armPlaybackTimeout(); } }}
      onError={() => { setAssetFailed(true); recover('The city animation could not load. You can still enter IntelliVest directly below.'); }} />
    <div className="cinematic-intro__readability" aria-hidden="true" />
    <h1 id={titleId} className="cinematic-intro__brand">IntelliVest</h1>
    <p id={descriptionId} className="cinematic-intro__sr-only">A sunset financial city. Start the cinematic introduction or skip directly to the IntelliVest website. The animation is muted.</p>
    <div className="cinematic-intro__centre">
      <div className="cinematic-intro__cta">
        <CinematicShinyButton onClick={start} disabled={busy} aria-describedby={statusId} />
        {reducedMotion && <p className="cinematic-intro__motion-note">Reduced motion enabled. Enter directly without playback.</p>}
      </div>
    </div>
    <div id={statusId} className="cinematic-intro__status" role="status" aria-live="polite">
      {error ? <><p>{error}</p><button type="button" className="cinematic-intro__direct" onClick={skip}>Enter website <span aria-hidden="true">→</span></button></>
        : buffering ? <p><span className="cinematic-intro__loading-dot" aria-hidden="true" />{phase === 'starting' ? 'Preparing your journey…' : 'Buffering the city scene…'}</p>
          : !ready && !reducedMotion ? <p>Loading the scene. Start whenever you’re ready.</p> : null}
    </div>
    {['welcome', 'finishing'].includes(phase) && <CinematicWelcome onComplete={finish} />}
    <button type="button" className="cinematic-intro__skip" onClick={skip}>Skip Intro <span aria-hidden="true">→</span></button>
  </dialog>;
}
