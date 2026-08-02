import React, { useRef, useState } from 'react';
import * as api from '../api';

const TABS = [
  { id: 'upload', label: 'File Upload', icon: 'fa-file-arrow-up' },
  { id: 'url',    label: 'Web URL',     icon: 'fa-link' },
  { id: 'text',   label: 'Paste Text',  icon: 'fa-paste' },
];

export default function IngestPage({ onNavigate, sessionId }) {
  const [tab, setTab] = useState('upload');
  // Tag every ingested document with the same scope the Chat page queries
  // (its session id) so uploads are immediately answerable -- without this,
  // documents land in a default scope no chat session ever reaches.
  const scope = sessionId ? `session:${sessionId}` : undefined;

  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const [url, setUrl] = useState('');

  const [text, setText] = useState('');
  const [textTitle, setTextTitle] = useState('');

  const [loading, setLoading] = useState(false);
  const [autoLoading, setAutoLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  function reset() { setError(''); setResult(null); }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    reset(); setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (scope) fd.append('scope', scope);
      setResult(await api.ingestUpload(fd));
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function handleUrl(e) {
    e.preventDefault();
    if (!url.trim()) return;
    reset(); setLoading(true);
    try { setResult(await api.ingestSource({ source: url.trim(), file_type: 'url', scope })); setUrl(''); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function handleText(e) {
    e.preventDefault();
    if (!text.trim()) return;
    reset(); setLoading(true);
    try {
      setResult(await api.ingestText({ text: text.trim(), title: textTitle.trim() || 'pasted_text', scope }));
      setText(''); setTextTitle('');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function handleAutoIngest() {
    reset(); setAutoLoading(true);
    try { setResult(await api.autoIngest()); }
    catch (err) { setError(err.message); }
    finally { setAutoLoading(false); }
  }

  const isAutoResult = result && result.chunks_added === undefined;
  const chunksAdded = result?.chunks_added ?? 0;

  return (
    <div style={{ maxWidth: 680 }}>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, background: 'var(--bg-input)', borderRadius: 'var(--r-md)', padding: 4 }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); reset(); }}
            style={{
              flex: 1, padding: '9px 0', fontSize: 13, fontWeight: tab === t.id ? 700 : 500,
              color: tab === t.id ? 'var(--primary)' : 'var(--text-secondary)',
              background: tab === t.id ? '#fff' : 'transparent',
              border: 'none', borderRadius: 'calc(var(--r-md) - 2px)',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: 7, transition: 'all .2s var(--ease)',
              boxShadow: tab === t.id ? 'var(--shadow-sm)' : 'none',
            }}
          >
            <i className={`fa-solid ${t.icon}`} style={{ fontSize: 12 }} />
            {t.label}
          </button>
        ))}
      </div>

      {/* File Upload */}
      {tab === 'upload' && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <span className="card-title"><i className="fa-solid fa-file-arrow-up" /> Upload Document</span>
            <span className="badge badge-primary">PDF · DOCX · TXT</span>
          </div>
          <form className="card-body" onSubmit={handleUpload}>
            <div
              style={{
                border: `2px dashed ${file ? 'var(--primary)' : 'var(--border)'}`,
                borderRadius: 'var(--r-md)', padding: '32px 24px', textAlign: 'center',
                background: file ? 'var(--primary-subtle)' : 'var(--bg-input)',
                transition: 'all .2s var(--ease)', marginBottom: 16, cursor: 'pointer',
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <i className="fa-solid fa-cloud-arrow-up" style={{ fontSize: 36, color: file ? 'var(--primary)' : 'var(--text-muted)', marginBottom: 10, display: 'block' }} />
              {file ? (
                <>
                  <div style={{ fontWeight: 700, color: 'var(--primary)', fontSize: 14 }}>{file.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{(file.size / 1024).toFixed(1)} KB · Click to change</div>
                </>
              ) : (
                <>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)' }}>Click to select or drag & drop</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>PDF, DOCX, or TXT up to any size</div>
                </>
              )}
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" style={{ display: 'none' }}
                onChange={(e) => { reset(); setFile(e.target.files[0] || null); }} />
            </div>
            <button className="btn btn-primary" type="submit" disabled={loading || !file} style={{ width: '100%' }}>
              {loading ? <><span className="spinner" /> Uploading & indexing...</> : <><i className="fa-solid fa-upload" /> Upload & Ingest</>}
            </button>
          </form>
        </div>
      )}

      {/* URL */}
      {tab === 'url' && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <span className="card-title"><i className="fa-solid fa-link" /> Ingest from URL</span>
            <span className="badge badge-accent">Web Scraper</span>
          </div>
          <form className="card-body" onSubmit={handleUrl}>
            <div className="form-group">
              <label className="form-label"><i className="fa-solid fa-globe" style={{ marginRight: 5 }} />Web URL</label>
              <input className="input" type="url" value={url} onChange={(e) => { reset(); setUrl(e.target.value); }}
                placeholder="https://example.com/article" />
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>The page will be scraped and its text content indexed.</p>
            </div>
            <button className="btn btn-primary" type="submit" disabled={loading || !url.trim()} style={{ width: '100%' }}>
              {loading ? <><span className="spinner" /> Fetching & indexing...</> : <><i className="fa-solid fa-cloud-arrow-down" /> Fetch & Ingest</>}
            </button>
          </form>
        </div>
      )}

      {/* Paste Text */}
      {tab === 'text' && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <span className="card-title"><i className="fa-solid fa-paste" /> Paste Text</span>
            <span className="badge badge-warning">Raw Text</span>
          </div>
          <form className="card-body" onSubmit={handleText}>
            <div className="form-group">
              <label className="form-label">Title <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
              <input className="input" value={textTitle} onChange={(e) => setTextTitle(e.target.value)}
                placeholder="e.g. Meeting Notes, Research Summary..." />
            </div>
            <div className="form-group">
              <label className="form-label">Text Content</label>
              <textarea className="input" value={text} onChange={(e) => { reset(); setText(e.target.value); }}
                placeholder="Paste your text here..." rows={9}
                style={{ resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }} />
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{text.length.toLocaleString()} characters</p>
            </div>
            <button className="btn btn-primary" type="submit" disabled={loading || !text.trim()} style={{ width: '100%' }}>
              {loading ? <><span className="spinner" /> Indexing...</> : <><i className="fa-solid fa-database" /> Ingest Text</>}
            </button>
          </form>
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ background: 'rgba(239,68,68,.06)', border: '1px solid rgba(239,68,68,.2)', borderRadius: 'var(--r-md)', padding: '14px 18px', display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 16 }}>
          <i className="fa-solid fa-circle-exclamation" style={{ color: '#ef4444', fontSize: 15, marginTop: 1, flexShrink: 0 }} />
          <span style={{ color: '#dc2626', fontSize: 13.5, lineHeight: 1.5 }}>{error}</span>
        </div>
      )}

      {/* Success result */}
      {result && !isAutoResult && (
        <div style={{ background: 'linear-gradient(135deg,rgba(99,102,241,.06),rgba(16,185,129,.04))', border: '1px solid rgba(99,102,241,.2)', borderRadius: 'var(--r-lg)', padding: '24px', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
            <div style={{ width: 44, height: 44, borderRadius: 'var(--r-md)', background: 'linear-gradient(135deg,var(--primary),var(--primary-dark))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18 }}>
              <i className="fa-solid fa-check" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>Successfully indexed!</div>
              <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 2 }}>Your document is ready to be queried</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 24, marginBottom: 18 }}>
            <div style={{ flex: 1, background: '#fff', borderRadius: 'var(--r-sm)', padding: '14px 18px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 26, fontWeight: 900, color: 'var(--primary)' }}>{chunksAdded}</div>
              <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.5px' }}>Chunks Added</div>
            </div>
            <div style={{ flex: 1, background: '#fff', borderRadius: 'var(--r-sm)', padding: '14px 18px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 26, fontWeight: 900 }}>{result.total_chunks}</div>
              <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.5px' }}>Total in Index</div>
            </div>
          </div>

          {result.sources?.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 18 }}>
              {result.sources.map((s, i) => (
                <span key={i} className="badge badge-success" style={{ fontSize: 12 }}>
                  <i className="fa-solid fa-file-circle-check" style={{ fontSize: 10 }} /> {s}
                </span>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onNavigate?.('chat')}>
              <i className="fa-solid fa-comments" /> Start Chatting
              <i className="fa-solid fa-arrow-right" style={{ marginLeft: 4, fontSize: 11 }} />
            </button>
            <button className="btn btn-secondary" onClick={() => setResult(null)}>
              <i className="fa-solid fa-plus" /> Add More
            </button>
          </div>
        </div>
      )}

      {/* Auto-ingest result */}
      {result && isAutoResult && (
        <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: '20px 24px', marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="fa-solid fa-wand-magic-sparkles" style={{ color: 'var(--primary)' }} /> Auto-Ingestion Complete
          </div>
          <div style={{ fontSize: 13, lineHeight: 1.8 }}>
            {result.ingested?.length > 0 && <div><strong style={{ color: '#22c55e' }}>Ingested:</strong> {result.ingested.join(', ')}</div>}
            {result.skipped?.length > 0 && <div><strong style={{ color: 'var(--text-muted)' }}>Skipped:</strong> {result.skipped.join(', ')}</div>}
            {result.failed?.length > 0 && <div><strong style={{ color: '#ef4444' }}>Failed:</strong> {result.failed.map((f) => f.file || f).join(', ')}</div>}
            {!result.ingested?.length && !result.skipped?.length && !result.failed?.length && (
              <span style={{ color: 'var(--text-muted)' }}>No files found in data directory.</span>
            )}
          </div>
          {result.ingested?.length > 0 && (
            <button className="btn btn-primary" style={{ marginTop: 14, width: '100%' }} onClick={() => onNavigate?.('chat')}>
              <i className="fa-solid fa-comments" /> Start Chatting
            </button>
          )}
        </div>
      )}

      {/* Auto Ingest */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><i className="fa-solid fa-wand-magic-sparkles" /> Auto Ingestion</span>
        </div>
        <div className="card-body">
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>
            Scan the data directory and automatically ingest all <code style={{ fontSize: 12 }}>.pdf</code>, <code style={{ fontSize: 12 }}>.docx</code>, <code style={{ fontSize: 12 }}>.txt</code> files found.
          </p>
          <button className="btn btn-secondary" onClick={handleAutoIngest} disabled={autoLoading}>
            {autoLoading ? <><span className="spinner" /> Scanning...</> : <><i className="fa-solid fa-magnifying-glass" /> Scan & Ingest</>}
          </button>
        </div>
      </div>
    </div>
  );
}
