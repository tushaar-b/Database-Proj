import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowRight, X } from 'lucide-react';
import './RecommendationTable.css';
import { QuoteLabel } from '../StockIntelligence.jsx';

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });
const decimal = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });
const missing = (value) => value == null || value === '';
const money = (value) => missing(value) ? '—' : currency.format(Number(value));
const number = (value) => missing(value) ? '—' : decimal.format(Number(value));
const allocation = (value) => missing(value) ? '—' : `${number(value)}%`;
const date = (value) => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value)) : null;

function RecommendationStatus({ value }) {
  return <span className="rec-status" data-status={value}>{String(value || 'Unknown').replaceAll('_', ' ')}</span>;
}

function RecommendationDetails({ item, onDismiss, returnFocusRef }) {
  const dialogRef = useRef(null);
  const closeRef = useRef(null);
  const dismissTimer = useRef(null);
  const [visible, setVisible] = useState(false);
  const titleId = useId();
  const securityId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    const previousOverflow = document.body.style.overflow;
    const trigger = returnFocusRef.current;
    document.body.style.overflow = 'hidden';
    // Native modal dialogs keep focus inside and make the workspace inert.
    dialog.showModal();
    closeRef.current?.focus();
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(dismissTimer.current);
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (trigger?.isConnected) trigger.focus({ preventScroll: true });
    };
  }, [returnFocusRef]);

  const dismiss = () => {
    if (dismissTimer.current != null) return;
    setVisible(false);
    dismissTimer.current = window.setTimeout(onDismiss, 220);
  };

  return createPortal(<dialog ref={dialogRef} className={`workspace-overlay recommendation-details-dialog${visible ? ' is-visible' : ''}`} aria-modal="true" aria-labelledby={titleId} aria-describedby={securityId} onCancel={(event) => { event.preventDefault(); dismiss(); }} onClick={(event) => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dismiss();
  }}>
    <header className="rec-details-header">
      <div><p className="rec-eyebrow">Recommendation details</p><h2 id={titleId}>Why was this stock recommended?</h2><p id={securityId} className="rec-details-security">{item.stock_ticker} — Recommendation Details</p></div>
      <button ref={closeRef} type="button" className="rec-close" onClick={dismiss} aria-label="Close recommendation details"><X size={20} /></button>
    </header>
    <div className="rec-details-content">
      <section className="rec-details-section" aria-labelledby={`${titleId}-summary`}>
        <h3 id={`${titleId}-summary`}>Recommendation summary</h3>
        <dl className="rec-summary">
          <div><dt>Security</dt><dd>{item.stock_ticker}</dd></div>
          <div><dt>Recommended amount</dt><dd>{money(item.recommended_amount)}</dd></div>
          <div><dt>Shares</dt><dd>{number(item.shares)}</dd></div>
          <div><dt>Target allocation</dt><dd>{allocation(item.target_allocation_pct)}</dd></div>
          <div><dt>Status</dt><dd><RecommendationStatus value={item.status_state} /></dd></div>
          {item.generated_timestamp && <div><dt>Generated</dt><dd>{date(item.generated_timestamp)}</dd></div>}
        </dl>
      </section>
      <section className="rec-details-section" aria-labelledby={`${titleId}-reason`}>
        <p className="rec-eyebrow">Complete saved explanation</p>
        <h3 id={`${titleId}-reason`}>Why this stock?</h3>
        {/* The API saves selection, history, risk policy and affordability in this
            string. Render it verbatim; do not infer metrics from prose. */}
        <p className="rec-explanation">{item.explanation || 'This saved recommendation has no selection explanation.'}</p>
      </section>
    </div>
    <footer className="rec-details-footer">Acceptance records investment intent only. It does not execute a brokerage trade.</footer>
  </dialog>, document.body);
}

export default function RecommendationTable({ items, busy, onDecide, allowDecision = true, showBatch = false, onAnalyse, label = 'Recommendations' }) {
  const [selectedId, setSelectedId] = useState(null);
  const returnFocusRef = useRef(null);
  const selected = items.find((item) => item.rec_id === selectedId);
  const dismiss = useCallback(() => setSelectedId(null), []);

  function openDetails(item, trigger) {
    trigger.focus({ preventScroll: true });
    returnFocusRef.current = trigger;
    setSelectedId(item.rec_id);
  }

  return <div className="recommendation-table">
    <div className="rec-table-scroll" role="region" aria-label={label} tabIndex={0}>
      <table aria-label={label}>
        <thead><tr><th scope="col">Security</th><th scope="col" className="rec-numeric">Recommended amount</th><th scope="col" className="rec-numeric">Target allocation</th><th scope="col" className="rec-numeric">Shares</th><th scope="col">Status</th><th scope="col">Details</th><th scope="col">Decision</th></tr></thead>
        <tbody>{items.map((item) => <tr key={item.rec_id} tabIndex={0} aria-label={`${item.stock_ticker}, view recommendation details`} aria-haspopup="dialog" onClick={(event) => {
          if (!event.target.closest('button, .rec-decisions')) openDetails(item, event.currentTarget);
        }} onKeyDown={(event) => {
          if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); openDetails(item, event.currentTarget); }
        }}>
          <td><div className="rec-security"><strong>{item.stock_ticker}</strong>{item.quote && <><small>Latest {money(item.quote.price)}</small><QuoteLabel quote={item.quote} /></>}{showBatch && <small>{item.batch_created_at ? `Batch ${date(item.batch_created_at)}` : 'Historical batch'}</small>}</div></td>
          <td className="rec-numeric">{money(item.recommended_amount)}{item.original_price != null && <small style={{ display: 'block' }}>Recorded at {money(item.original_price)}</small>}{item.requires_regeneration && <small style={{ display: 'block' }}>Revalidation needed</small>}</td>
          <td className="rec-numeric">{allocation(item.target_allocation_pct)}</td>
          <td className="rec-numeric">{number(item.shares)}</td>
          <td><RecommendationStatus value={item.status_state} /></td>
          <td><button type="button" className="rec-details-action" aria-label={`View details for ${item.stock_ticker}`} aria-haspopup="dialog" onClick={(event) => { event.stopPropagation(); openDetails(item, event.currentTarget); }}>View Details <ArrowRight size={14} aria-hidden="true" /></button>{onAnalyse && <button className="rec-details-action" onClick={(event) => { event.stopPropagation(); onAnalyse(item); }}>Analyse Stock</button>}</td>
          <td>{allowDecision && item.status_state === 'PENDING' ? <div className="rec-decisions" onClick={(event) => event.stopPropagation()}>
            <button type="button" className="rec-decision rec-accept" disabled={busy} aria-label={`Accept ${item.stock_ticker}`} onClick={() => onDecide(item, 'ACCEPTED')}>Accept</button>
            <button type="button" className="rec-decision rec-decline" disabled={busy} aria-label={`Decline ${item.stock_ticker}`} onClick={() => onDecide(item, 'REJECTED')}>Decline</button>
          </div> : <span className="rec-recorded">{item.status_state === 'SUPERSEDED' ? 'Superseded' : 'Recorded'}</span>}</td>
        </tr>)}</tbody>
      </table>
    </div>
    {selected && <RecommendationDetails key={selected.rec_id} item={selected} onDismiss={dismiss} returnFocusRef={returnFocusRef} />}
  </div>;
}
