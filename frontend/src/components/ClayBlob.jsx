import './ClayBlob.css';

// Decorative only: add a tint modifier and position it inside an isolated section.
export default function ClayBlob({ tint = 'coral', className = '' }) {
  return <span aria-hidden="true" className={`clay-blob clay-blob--${tint} ${className}`}><span className="clay-blob__puff" /></span>;
}
