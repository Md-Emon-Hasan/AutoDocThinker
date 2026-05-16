import React, { useState, useEffect } from 'react';
import * as api from '../api';

const MODE_META = {
  naive: { icon: 'fa-solid fa-bolt', desc: 'Fast single-pass retrieval' },
  advanced: { icon: 'fa-solid fa-brain', desc: 'Multi-step re-ranking pipeline' },
  crag: { icon: 'fa-solid fa-microscope', desc: 'Corrective RAG with confidence scoring' },
  self_rag: { icon: 'fa-solid fa-rotate', desc: 'Self-reflective iterative refinement' },
};

export default function AdminPage() {
  const [summary, setSummary] = useState(null);
  const [ragModes, setRagModes] = useState([]);
  const [ragProfiles, setRagProfiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAdminSummary().catch(() => null),
      api.getRagModes().catch(() => ({ modes: [] })),
      api.getRagProfiles().catch(() => []),
    ]).then(([sum, modes, profiles]) => {
      setSummary(sum);
      setRagModes(modes?.modes || []);
      setRagProfiles(profiles || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="empty-state"><div className="spinner spinner-lg" /><p style={{ marginTop: 14 }}>Loading admin data...</p></div>;
  }

  return (
    <div style={{ maxWidth: 840 }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 14, lineHeight: 1.6 }}>
        <i className="fa-solid fa-circle-info" style={{ color: 'var(--primary)', marginRight: 6 }} />
        Monitor your AutoDocThinker instance — domains, chunks, RAG modes, and pipeline profiles.
      </p>

      <div className="stats-grid">
        <div className="stat-card purple">
          <div className="stat-icon purple"><i className="fa-solid fa-layer-group" /></div>
          <div className="stat-value">{summary?.domains?.length ?? 0}</div>
          <div className="stat-label">Domains</div>
        </div>
        <div className="stat-card cyan">
          <div className="stat-icon cyan"><i className="fa-solid fa-cubes" /></div>
          <div className="stat-value">{summary?.chunks ?? 0}</div>
          <div className="stat-label">Total Chunks</div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon green"><i className="fa-solid fa-microchip" /></div>
          <div className="stat-value">{ragModes.length}</div>
          <div className="stat-label">RAG Modes</div>
        </div>
        <div className="stat-card amber">
          <div className="stat-icon amber"><i className="fa-solid fa-diagram-project" /></div>
          <div className="stat-value">{ragProfiles.length}</div>
          <div className="stat-label">RAG Profiles</div>
        </div>
      </div>

      {summary?.domains?.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header"><span className="card-title"><i className="fa-solid fa-sitemap" /> Registered Domains</span></div>
          <div className="card-body"><div className="chip-group">
            {summary.domains.map((d) => <span key={d} className="chip"><i className="fa-solid fa-circle" style={{ fontSize: 6 }} />{d}</span>)}
          </div></div>
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header"><span className="card-title"><i className="fa-solid fa-gears" /> Available RAG Modes</span></div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: 12 }}>
            {ragModes.map((m) => {
              const meta = MODE_META[m] || { icon: 'fa-solid fa-circle', desc: '' };
              return (
                <div key={m} style={{ padding: '14px 18px', background: 'var(--bg-input)', borderRadius: 'var(--r-md)', border: '1px solid var(--border-light)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <i className={meta.icon} style={{ color: 'var(--primary)', fontSize: 15 }} />
                    <strong style={{ fontSize: 14 }}>{m.charAt(0).toUpperCase() + m.slice(1).replace('_', ' ')}</strong>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{meta.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {ragProfiles.length > 0 && (
        <div className="card">
          <div className="card-header"><span className="card-title"><i className="fa-solid fa-table-cells" /> RAG Profiles Matrix</span></div>
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Domain</th><th>Supported Modes</th></tr></thead>
              <tbody>
                {ragProfiles.map((p, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}><i className="fa-solid fa-folder" style={{ marginRight: 8, color: 'var(--primary)', fontSize: 13 }} />{p.domain}</td>
                    <td><div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{p.rag_modes?.map((m) => <span key={m} className="badge badge-primary">{m}</span>)}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
