import React from 'react';

export default function App() {
  return (
    <main style={{ padding: '3rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', background: 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '0.5rem' }}>
          IntelliVest Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
          Closed-Loop Financial Analytics & Affordability-Driven Portfolio Management
        </p>
      </header>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <article style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem', color: 'var(--accent-cyan)' }}>Personal Cash Flow</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Income and mandatory expense tracking with surplus evaluation and investable buffer calculations.
          </p>
        </article>

        <article style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem', color: 'var(--accent-cyan)' }}>In-Engine SQL Risk Meters</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Real-time rolling volatility, 95% Parametric VaR, Historical VaR, and Sector HHI concentration.
          </p>
        </article>

        <article style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem', color: 'var(--accent-cyan)' }}>Closed-Loop Rebalance</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            SERIALIZABLE transaction isolation and automated allocation cap drift throttling.
          </p>
        </article>
      </section>
    </main>
  );
}
