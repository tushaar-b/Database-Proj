import { useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';

export default function WorkspaceModal({ title, eyebrow, onClose, onSubmit, children }) {
  const dialogRef = useRef(null);
  const closeRef = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = dialogRef.current;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.showModal();
    closeRef.current?.focus();
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true });
    };
  }, []);
  return <dialog ref={dialogRef} className="workspace-modal" aria-modal="true" aria-labelledby={titleId} onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();
  }}>
    <form className="modal-card" onSubmit={onSubmit}>
      <header className="modal-heading"><div><p className="eyebrow">{eyebrow}</p><h2 id={titleId}>{title}</h2></div><button ref={closeRef} type="button" className="modal-close icon-button" onClick={onClose} aria-label="Close editor"><X size={18} /></button></header>
      {children}
    </form>
  </dialog>;
}
