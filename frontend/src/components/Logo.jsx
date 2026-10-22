import { useId } from 'react';
import './Logo.css';

export default function Logo({ className = '' }) {
  const gradient = useId();
  return <a className={`brand-logo ${className}`.trim()} href="#top" aria-label="Intellivest home">
    <svg className="brand-logo__mark" viewBox="0 0 40 40" role="img" aria-hidden="true">
      <defs><linearGradient id={gradient}><stop stopColor="var(--indigo)" /><stop offset=".45" stopColor="var(--violet)" /><stop offset="1" stopColor="var(--coral)" /></linearGradient></defs>
      <circle cx="20" cy="20" r="18.25" fill="none" stroke={`url(#${gradient})`} strokeWidth="1.7" />
      <path d="M9.5 24.5 16 18l4.2 4.1L30.5 11.5M24 11.5h6.5V18" fill="none" stroke={`url(#${gradient})`} strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="18" r="1.5" fill="currentColor" />
    </svg>
    <span className="brand-logo__word">Intelli<span>vest</span></span>
  </a>;
}
