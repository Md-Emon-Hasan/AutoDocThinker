import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatPage from './components/ChatPage';
import DomainsPage from './components/DomainsPage';
import IngestPage from './components/IngestPage';
import IndexPage from './components/IndexPage';
import AdminPage from './components/AdminPage';
import * as api from './api';

const PAGE_INFO = {
  chat: { title: 'Chat', sub: 'AI-powered document question answering', icon: 'fa-regular fa-comment-dots' },
  domains: { title: 'Domains', sub: 'Browse knowledge domains & configurations', icon: 'fa-solid fa-layer-group' },
  ingest: { title: 'Ingestion', sub: 'Import and process documents', icon: 'fa-solid fa-cloud-arrow-up' },
  index: { title: 'Index', sub: 'Manage the hybrid search index', icon: 'fa-solid fa-database' },
  admin: { title: 'Admin', sub: 'System overview & RAG configuration', icon: 'fa-solid fa-sliders' },
};

function lsGet(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}
function lsSet(key, val) {
  try { localStorage.setItem(key, val); } catch {}
}

export default function App() {
  const [page, setPage] = useState('chat');
  const [serverUp, setServerUp] = useState(null); // null = checking
  const [domains, setDomains] = useState([]);
  const [ragModes, setRagModes] = useState(['naive', 'advanced', 'crag', 'self_rag']);
  const [domain, setDomain] = useState(() => lsGet('adt_domain', 'general'));
  const [ragMode, setRagMode] = useState(() => lsGet('adt_rag_mode', 'advanced'));

  useEffect(() => {
    api.getHealth().then(() => setServerUp(true)).catch(() => setServerUp(false));
    api.getDomains().then(setDomains).catch(() => {});
    api.getRagModes().then((r) => setRagModes(r.modes || [])).catch(() => {});
  }, []);

  function handleDomainChange(val) {
    setDomain(val);
    lsSet('adt_domain', val);
  }

  function handleRagModeChange(val) {
    setRagMode(val);
    lsSet('adt_rag_mode', val);
  }

  const info = PAGE_INFO[page];

  return (
    <div className="app-layout">
      <Sidebar
        page={page} setPage={setPage} serverUp={serverUp}
        domain={domain} ragMode={ragMode}
      />
      <main className="main-content">
        {serverUp === false && (
          <div style={{
            background: 'rgba(239,68,68,.08)', borderBottom: '1px solid rgba(239,68,68,.2)',
            padding: '10px 24px', display: 'flex', alignItems: 'center', gap: 10,
            fontSize: 13, color: '#dc2626',
          }}>
            <i className="fa-solid fa-triangle-exclamation" />
            <strong>Backend offline.</strong> Run <code style={{ background: 'rgba(239,68,68,.1)', padding: '1px 6px', borderRadius: 4, fontSize: 12 }}>python run.py</code> inside the <code style={{ background: 'rgba(239,68,68,.1)', padding: '1px 6px', borderRadius: 4, fontSize: 12 }}>backend/</code> folder, then refresh.
          </div>
        )}
        {page !== 'chat' && (
          <header className="main-header">
            <div>
              <h1><i className={info.icon} style={{ marginRight: 10, fontSize: 20 }} />{info.title}</h1>
              <div className="main-header-sub">{info.sub}</div>
            </div>
            <div className="main-header-actions">
              {serverUp === true
                ? <span className="badge badge-success"><i className="fa-solid fa-circle" style={{ fontSize: 7 }} /> Online</span>
                : serverUp === false
                  ? <span className="badge badge-danger"><i className="fa-solid fa-circle" style={{ fontSize: 7 }} /> Offline</span>
                  : <span className="badge" style={{ background: 'var(--bg-input)', color: 'var(--text-muted)' }}>Connecting…</span>
              }
            </div>
          </header>
        )}
        {page === 'chat' ? (
          <ChatPage
            domains={domains} ragModes={ragModes} onNavigate={setPage}
            domain={domain} ragMode={ragMode}
            onDomainChange={handleDomainChange} onRagModeChange={handleRagModeChange}
          />
        ) : (
          <div className="main-body">
            {page === 'domains' && <DomainsPage />}
            {page === 'ingest' && <IngestPage onNavigate={setPage} />}
            {page === 'index' && <IndexPage onNavigate={setPage} />}
            {page === 'admin' && <AdminPage />}
          </div>
        )}
      </main>
    </div>
  );
}
