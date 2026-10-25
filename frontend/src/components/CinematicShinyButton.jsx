import { ArrowRight } from 'lucide-react';
import './CinematicShinyButton.css';

export default function CinematicShinyButton({ onClick, disabled = false, children = 'Dive into the World of Finance', ...props }) {
  return <button type="button" className="cinematic-shiny-button" onClick={onClick} disabled={disabled} {...props}>
    <span className="cinematic-shiny-button__surface" aria-hidden="true" />
    <span className="cinematic-shiny-button__dots" aria-hidden="true" />
    <span className="cinematic-shiny-button__shimmer" aria-hidden="true" />
    <span className="cinematic-shiny-button__label">{children}<ArrowRight className="cinematic-shiny-button__arrow" size={19} strokeWidth={1.7} aria-hidden="true" /></span>
  </button>;
}
