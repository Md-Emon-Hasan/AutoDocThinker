import React from 'react';

const PAGES = [
  { id: 'chat', icon: 'fa-regular fa-comment-dots', label: 'Chat' },
  { id: 'domains', icon: 'fa-solid fa-layer-group', label: 'Domains' },
  { id: 'ingest', icon: 'fa-solid fa-cloud-arrow-up', label: 'Ingestion' },
  { id: 'index', icon: 'fa-solid fa-database', label: 'Index' },
  { id: 'admin', icon: 'fa-solid fa-sliders', label: 'Admin' },
];

const RAG_MODE_META = {
  naive:    { label: 'Naive RAG',    icon: 'fa-bolt',        color: '#f59e0b' },
  advanced: { label: 'Advanced RAG', icon: 'fa-layer-group', color: '#6366f1' },
  crag:     { label: 'CRAG',         icon: 'fa-shield-check',color: '#8b5cf6' },
  self_rag: { label: 'Self-RAG',     icon: 'fa-rotate',      color: '#06b6d4' },
};

function toLabel(str) {
  return (str || 'general').split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export default function Sidebar({ page, setPage, serverUp, domain, ragMode }) {
  const domainLabel = toLabel(domain);
  const modeMeta = RAG_MODE_META[ragMode] || { label: toLabel(ragMode), icon: 'fa-microchip', color: '#6366f1' };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <i className="fa-solid fa-brain" />
          </div>
          <div>
            <div className="sidebar-title">AutoDocThinker</div>
            <div className="sidebar-subtitle">AI Document Intelligence</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {PAGES.map((p) => (
          <button
            key={p.id}
            className={`nav-item${page === p.id ? ' active' : ''}`}
            onClick={() => setPage(p.id)}
            id={`nav-${p.id}`}
          >
            <span className="nav-icon"><i className={p.icon} /></span>
            {p.label}
          </button>
        ))}
      </nav>

      {/* Active Profile */}
      <div style={{ padding: '14px 14px 10px', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.8px', marginBottom: 8 }}>
          Active Profile
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', background: 'var(--primary-subtle)', borderRadius: 'var(--r-sm)', border: '1px solid rgba(99,102,241,.15)' }}>
            <i className="fa-solid fa-layer-group" style={{ fontSize: 11, color: 'var(--primary)', width: 14, textAlign: 'center' }} />
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 9.5, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>Domain</div>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{domainLabel}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', background: `${modeMeta.color}12`, borderRadius: 'var(--r-sm)', border: `1px solid ${modeMeta.color}30` }}>
            <i className={`fa-solid ${modeMeta.icon}`} style={{ fontSize: 11, color: modeMeta.color, width: 14, textAlign: 'center' }} />
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 9.5, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>RAG Mode</div>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{modeMeta.label}</div>
            </div>
          </div>
        </div>
        {page !== 'chat' && (
          <button
            onClick={() => setPage('chat')}
            style={{
              width: '100%', marginTop: 8, padding: '6px 0', fontSize: 11.5, fontWeight: 600,
              color: 'var(--primary)', background: 'transparent', border: '1px solid rgba(99,102,241,.2)',
              borderRadius: 'var(--r-sm)', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--primary-subtle)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          >
            <i className="fa-solid fa-pen-to-square" style={{ fontSize: 10 }} /> Change in Chat
          </button>
        )}
      </div>

      {/* Author */}
      <div style={{
        margin: '0 12px 12px', padding: '12px 14px',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(135deg,rgba(99,102,241,.05),rgba(6,182,212,.03))',
        border: '1px solid rgba(99,102,241,.12)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
            background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 13, fontWeight: 700,
            boxShadow: '0 2px 8px rgba(99,102,241,.3)',
          }}>M</div>
          <div>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text)', lineHeight: 1.2 }}>Md Emon Hasan</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 500, marginTop: 1 }}>ML Engineer</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 5 }}>
          {[
            { href: 'mailto:emon.mlengineer@gmail.com', icon: 'fa-solid fa-envelope', title: 'Email', color: '#6366f1' },
            { href: 'https://www.linkedin.com/in/md-emon-hasan-695483237/', icon: 'fa-brands fa-linkedin', title: 'LinkedIn', color: '#0077b5' },
            { href: 'https://github.com/Md-Emon-Hasan', icon: 'fa-brands fa-github', title: 'GitHub', color: '#24292f' },
            { href: 'https://www.facebook.com/mdemon.hasan2001/', icon: 'fa-brands fa-facebook', title: 'Facebook', color: '#1877f2' },
          ].map(({ href, icon, title, color }) => (
            <a
              key={title}
              href={href}
              target="_blank"
              rel="noreferrer"
              title={title}
              style={{
                flex: 1, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)',
                color: 'var(--text-muted)', fontSize: 12, textDecoration: 'none',
                background: '#fff', transition: 'all .18s var(--ease)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = color; e.currentTarget.style.borderColor = color + '55'; e.currentTarget.style.background = color + '10'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = '#fff'; e.currentTarget.style.transform = 'none'; }}
            >
              <i className={icon} />
            </a>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot${serverUp ? '' : ' offline'}`} />
          <i className={`fa-solid ${serverUp ? 'fa-signal' : 'fa-triangle-exclamation'}`} style={{ fontSize: 11 }} />
          {serverUp ? 'Backend Connected' : serverUp === false ? 'Backend Offline' : 'Connecting…'}
        </div>
        <div className="sidebar-version">
          <i className="fa-regular fa-bookmark" style={{ marginRight: 5, fontSize: 10 }} />
          v3.0.0 · RAG Engine
        </div>
      </div>
    </aside>
  );
}
