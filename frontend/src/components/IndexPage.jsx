import React, { useState, useEffect } from 'react';
import * as api from '../api';

function ConfirmModal({ name, onConfirm, onCancel }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
    }}>
      <div style={{ background: '#fff', borderRadius: 'var(--r-lg)', padding: '28px 32px', width: 380, boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 'var(--r-md)', background: 'rgba(239,68,68,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
          <i className="fa-solid fa-trash-can" style={{ color: '#ef4444', fontSize: 20 }} />
        </div>
        <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>Remove Document</div>
        <div style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 22 }}>
          Remove <strong>&ldquo;{name}&rdquo;</strong> from the index? This cannot be undone. Re-upload the file to index it again.
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onCancel}>Cancel</button>
          <button className="btn btn-danger" style={{ flex: 1 }} onClick={onConfirm}>
            <i className="fa-solid fa-trash-can" /> Remove
          </button>
        </div>
      </div>
    </div>
  );
}

export default function IndexPage({ onNavigate }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [confirmTarget, setConfirmTarget] = useState(null); // {source_id, name}
  const [error, setError] = useState(null);

  async function fetchStatus() {
    setLoading(true);
    try { setStatus(await api.getIndexStatus()); }
    catch { setStatus(null); }
    finally { setLoading(false); }
  }

  useEffect(() => { fetchStatus(); }, []);

  async function handleRemoveSource(source_id) {
    setRemovingId(source_id);
    setError(null);
    try {
      await api.removeSource(source_id);
      await fetchStatus();
    } catch (e) { setError(e.message || 'Failed to remove document'); }
    finally { setRemovingId(null); setConfirmTarget(null); }
  }

  async function handleClearAll() {
    setClearing(true);
    setError(null);
    try { await api.clearIndex(); await fetchStatus(); }
    catch (e) { setError(e.message || 'Failed to clear index'); }
    finally { setClearing(false); setConfirmTarget(null); }
  }

  const sources = status?.source_details ?? [];
  const totalChunks = status?.total_chunks ?? 0;

  if (loading) {
    return (
      <div className="empty-state">
        <span className="spinner spinner-lg" />
        <p style={{ marginTop: 14 }}>Loading index...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 760 }}>
      {/* Confirm modal */}
      {confirmTarget && (
        <ConfirmModal
          name={confirmTarget.name}
          onConfirm={() => confirmTarget.all ? handleClearAll() : handleRemoveSource(confirmTarget.source_id)}
          onCancel={() => setConfirmTarget(null)}
        />
      )}

      {error && (
        <div style={{
          background: 'rgba(239,68,68,.08)', border: '1px solid rgba(239,68,68,.25)', color: '#ef4444',
          borderRadius: 'var(--r-md)', padding: '10px 14px', fontSize: 13, marginBottom: 16,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <i className="fa-solid fa-triangle-exclamation" />
          <span style={{ flex: 1 }}>{error}</span>
          <button className="btn btn-sm" onClick={() => setError(null)} style={{ background: 'transparent', border: 'none', color: '#ef4444' }}>
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', marginBottom: 24 }}>
        <div className="stat-card purple">
          <div className="stat-icon purple"><i className="fa-solid fa-cubes" /></div>
          <div className="stat-value">{totalChunks}</div>
          <div className="stat-label">Total Chunks</div>
        </div>
        <div className="stat-card cyan">
          <div className="stat-icon cyan"><i className="fa-solid fa-file-lines" /></div>
          <div className="stat-value">{sources.length}</div>
          <div className="stat-label">Indexed Sources</div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon green"><i className="fa-solid fa-circle-check" /></div>
          <div className="stat-value" style={{ fontSize: 18, paddingTop: 4 }}>
            {sources.length > 0 ? <span style={{ color: 'var(--success)' }}>Ready</span> : <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>Empty</span>}
          </div>
          <div className="stat-label">Index Status</div>
        </div>
      </div>

      {/* Empty state */}
      {sources.length === 0 ? (
        <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '48px 24px', textAlign: 'center', marginBottom: 20 }}>
          <i className="fa-solid fa-inbox" style={{ fontSize: 40, color: 'var(--text-muted)', opacity: .3, marginBottom: 16, display: 'block' }} />
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>No documents indexed yet</div>
          <div style={{ fontSize: 13.5, color: 'var(--text-secondary)', maxWidth: 360, margin: '0 auto 20px' }}>
            Upload a PDF, paste a URL, or add text in the Ingestion panel to get started.
          </div>
          <button className="btn btn-primary" onClick={() => onNavigate?.('ingest')}>
            <i className="fa-solid fa-cloud-arrow-up" /> Go to Ingestion
          </button>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <span className="card-title"><i className="fa-solid fa-list-check" /> Indexed Documents</span>
            <span className="badge badge-success">{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
          </div>
          <div style={{ padding: '8px 0' }}>
            {sources.map((s, i) => (
              <div key={s.source_id} style={{
                display: 'flex', alignItems: 'center', gap: 14, padding: '13px 24px',
                borderBottom: i < sources.length - 1 ? '1px solid var(--border-light)' : 'none',
                transition: 'background .15s var(--ease)',
              }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--primary-subtle)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ width: 36, height: 36, borderRadius: 'var(--r-sm)', background: 'var(--bg-input)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <i className={`fa-solid ${getSourceIcon(s.name)}`} style={{ color: 'var(--primary)', fontSize: 14 }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13.5, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.name}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                    id: {s.source_id}
                  </div>
                </div>
                <button
                  className="btn btn-sm"
                  disabled={removingId === s.source_id}
                  onClick={() => setConfirmTarget(s)}
                  style={{
                    background: 'rgba(239,68,68,.06)', color: '#ef4444', border: '1px solid rgba(239,68,68,.15)',
                    padding: '6px 12px', flexShrink: 0,
                  }}
                >
                  {removingId === s.source_id
                    ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                    : <><i className="fa-solid fa-trash-can" style={{ fontSize: 11 }} /> Remove</>
                  }
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={fetchStatus}>
          <i className="fa-solid fa-arrows-rotate" /> Refresh
        </button>
        {sources.length > 0 && (
          <>
            <button className="btn btn-primary" onClick={() => onNavigate?.('chat')}>
              <i className="fa-solid fa-comments" /> Chat with Documents
            </button>
            <button className="btn btn-danger" disabled={clearing}
              onClick={() => setConfirmTarget({ name: 'ALL documents', all: true })}
              style={{ marginLeft: 'auto' }}
            >
              <i className="fa-solid fa-trash-can" /> {clearing ? 'Clearing...' : 'Clear All'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function getSourceIcon(name) {
  const n = (name || '').toLowerCase();
  if (n.endsWith('.pdf')) return 'fa-file-pdf';
  if (n.endsWith('.docx') || n.endsWith('.doc')) return 'fa-file-word';
  if (n.endsWith('.txt')) return 'fa-file-lines';
  if (n.startsWith('http') || n.startsWith('www')) return 'fa-globe';
  if (n === 'pasted_text' || n.includes('pasted')) return 'fa-paste';
  return 'fa-file';
}
