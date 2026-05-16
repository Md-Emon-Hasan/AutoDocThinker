import React, { useState, useRef, useEffect } from 'react';
import * as api from '../api';

const FALLBACK_DOMAINS = [
  { name: 'general', label: 'General' },
  { name: 'legal', label: 'Legal' },
  { name: 'medical', label: 'Medical' },
  { name: 'finance', label: 'Finance' },
  { name: 'education', label: 'Education' },
  { name: 'technical', label: 'Technical' },
  { name: 'customer_support', label: 'Customer Support' },
];

const SUGGESTIONS = [
  'Summarize the key points of this document',
  'What are the main risks mentioned?',
  'Explain the technical architecture',
  'List all action items and deadlines',
];

const RAG_LABELS = {
  naive: { label: 'Naive', desc: 'Fast single-pass retrieval' },
  advanced: { label: 'Advanced', desc: 'Multi-step re-ranking' },
  crag: { label: 'CRAG', desc: 'Corrective RAG with confidence scoring' },
  self_rag: { label: 'Self-RAG', desc: 'Self-reflective iterative refinement' },
};

function TypingIndicator() {
  return (
    <div className="msg-row assistant">
      <div className="msg-avatar"><i className="fa-solid fa-robot" style={{ fontSize: 14 }} /></div>
      <div className="msg-bubble">
        <div className="typing-dots"><span /><span /><span /></div>
      </div>
    </div>
  );
}

function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <details className="msg-sources">
      <summary><i className="fa-solid fa-paperclip" /> {sources.length} source{sources.length > 1 ? 's' : ''} referenced</summary>
      <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 12 }}>
        {sources.map((s, i) => (
          <li key={i} style={{ marginBottom: 4 }}>{s.source || s.title || JSON.stringify(s)}</li>
        ))}
      </ul>
    </details>
  );
}

function renderMarkdown(text) {
  if (!text) return '';
  let html = text;

  // Code blocks (must be first)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
    `<pre class="code-block${lang ? ` lang-${lang}` : ''}"><code>${code.trim()}</code></pre>`
  );

  // Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr class="md-hr"/>');

  // Bold + italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');

  // Numbered lists — group consecutive items
  html = html.replace(/((?:^[0-9]+\. .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(line =>
      `<li>${line.replace(/^[0-9]+\. /, '')}</li>`
    ).join('');
    return `<ol class="md-ol">${items}</ol>`;
  });

  // Unordered lists — group consecutive items
  html = html.replace(/((?:^[-*] .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(line =>
      `<li>${line.replace(/^[-*] /, '')}</li>`
    ).join('');
    return `<ul class="md-ul">${items}</ul>`;
  });

  // Remaining newlines → line breaks (skip inside block elements)
  html = html.replace(/\n{2,}/g, '</p><p class="md-p">');
  html = html.replace(/\n/g, '<br/>');
  html = `<p class="md-p">${html}</p>`;

  // Clean up empty paragraphs around block elements
  html = html.replace(/<p class="md-p">(<(?:h[123]|ul|ol|pre|blockquote|hr)[^>]*>)/g, '$1');
  html = html.replace(/(<\/(?:h[123]|ul|ol|pre|blockquote)>)<\/p>/g, '$1');

  return html;
}

function MessageBubble({ role, content, sources }) {
  const isUser = role === 'user';
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return (
    <div className={`msg-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="msg-avatar">
        <i className={`fa-solid ${isUser ? 'fa-user' : 'fa-robot'}`} style={{ fontSize: 14 }} />
      </div>
      <div className="msg-body">
        <div className="msg-meta">
          <span className="msg-name">{isUser ? 'You' : 'AutoDocThinker'}</span>
          <span className="msg-time">{now}</span>
        </div>
        <div className="msg-bubble">
          <div dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
          {!isUser && <SourcesList sources={sources} />}
        </div>
      </div>
    </div>
  );
}

export default function ChatPage({ domains, ragModes, onNavigate, domain, ragMode, onDomainChange, onRagModeChange }) {
  const domainList = domains.length > 0 ? domains : FALLBACK_DOMAINS;
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastSources, setLastSources] = useState({});
  const [indexCount, setIndexCount] = useState(null);
  const [profileToast, setProfileToast] = useState('');
  const scrollRef = useRef(null);
  const toastTimer = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  useEffect(() => {
    api.getIndexStatus()
      .then((s) => setIndexCount(s.total_chunks ?? 0))
      .catch(() => setIndexCount(0));
  }, []);

  function showToast(msg) {
    setProfileToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setProfileToast(''), 2200);
  }

  async function applyProfile(newDomain, newMode) {
    if (sessionId) {
      try {
        await api.selectProfile(sessionId, { domain: newDomain, rag_mode: newMode });
      } catch { /* session might not exist yet, ignore */ }
    }
    showToast(`${RAG_LABELS[newMode]?.label || newMode} · ${domainList.find((d) => d.name === newDomain)?.label || newDomain}`);
  }

  async function handleDomainChange(val) {
    onDomainChange?.(val);
    await applyProfile(val, ragMode);
  }

  async function handleRagModeChange(val) {
    onRagModeChange?.(val);
    await applyProfile(domain, val);
  }

  async function doSend(text) {
    if (!text.trim() || loading) return;
    const msg = text.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      let sid = sessionId;
      if (!sid) {
        const sess = await api.createSession();
        sid = sess.session_id;
        setSessionId(sid);
        await api.selectProfile(sid, { domain, rag_mode: ragMode });
      }
      const res = await api.sendMessage(sid, { message: msg });
      const idx = messages.length + 1;
      setLastSources((prev) => ({ ...prev, [idx]: res.sources }));
      setMessages((prev) => [...prev, { role: 'assistant', content: res.answer, _idx: idx }]);
    } catch (e) {
      const msg = e.message || 'Unknown error';
      const isRateLimit = msg.toLowerCase().includes('rate limit') || msg.includes('429');
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: isRateLimit
          ? `⚠️ **Groq API Daily Limit Reached**\n\nThe free-tier daily token quota (100,000 tokens/day) has been exhausted.\n\n**To fix this:**\n- Wait until midnight UTC for the quota to reset automatically.\n- Or upgrade your Groq plan at [console.groq.com/settings/billing](https://console.groq.com/settings/billing)\n\n*Error: ${msg}`
          : `❌ **Error:** ${msg}`,
      }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); doSend(input); }
  }

  function handleNewChat() {
    setSessionId(null); setMessages([]); setLastSources({});
  }

  const hasDocuments = indexCount !== null && indexCount > 0;
  const isEmpty = messages.length === 0 && !loading;

  return (
    <div className="chat-container">
      {/* Toolbar */}
      <div className="chat-toolbar">
        <label><i className="fa-solid fa-layer-group" style={{ marginRight: 5 }} />Domain</label>
        <select value={domain} onChange={(e) => handleDomainChange(e.target.value)} id="chat-domain-select">
          {domainList.map((d) => <option key={d.name} value={d.name}>{d.label}</option>)}
        </select>
        <div className="chat-toolbar-sep" />
        <label><i className="fa-solid fa-microchip" style={{ marginRight: 5 }} />RAG Mode</label>
        <select value={ragMode} onChange={(e) => handleRagModeChange(e.target.value)} id="chat-rag-select"
          title={RAG_LABELS[ragMode]?.desc}>
          {ragModes.map((m) => <option key={m} value={m}>{RAG_LABELS[m]?.label || m}</option>)}
        </select>

        {/* Profile applied toast */}
        {profileToast && (
          <span style={{
            fontSize: 11.5, color: 'var(--primary)', fontWeight: 600,
            background: 'var(--primary-subtle)', padding: '4px 10px',
            borderRadius: 'var(--r-full)', border: '1px solid rgba(99,102,241,.2)',
            animation: 'fadeSlideIn .2s var(--ease)',
            display: 'flex', alignItems: 'center', gap: 5,
          }}>
            <i className="fa-solid fa-circle-check" style={{ fontSize: 10 }} /> {profileToast}
          </span>
        )}

        <div style={{ flex: 1 }} />

        {/* Document count pill */}
        {indexCount !== null && (
          <span
            onClick={() => onNavigate?.('index')}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '5px 12px', borderRadius: 'var(--r-full)',
              background: hasDocuments ? 'rgba(16,185,129,.08)' : 'rgba(245,158,11,.08)',
              color: hasDocuments ? '#059669' : '#d97706',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
              border: `1px solid ${hasDocuments ? 'rgba(16,185,129,.2)' : 'rgba(245,158,11,.2)'}`,
              transition: 'all .15s',
            }}
          >
            <i className={`fa-solid ${hasDocuments ? 'fa-database' : 'fa-triangle-exclamation'}`} style={{ fontSize: 10 }} />
            {hasDocuments ? `${indexCount} chunks indexed` : 'No documents'}
          </span>
        )}

        <button className="btn btn-ghost btn-sm" onClick={handleNewChat} id="btn-new-chat">
          <i className="fa-solid fa-plus" /> New Chat
        </button>
      </div>

      {/* Messages area */}
      <div className="chat-messages" ref={scrollRef}>
        {isEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty-icon"><i className="fa-solid fa-brain" /></div>

            {hasDocuments ? (
              <>
                <h2>Ask anything about your documents</h2>
                <p style={{ color: 'var(--text-muted)' }}>
                  <i className="fa-solid fa-database" style={{ color: 'var(--success)', marginRight: 5 }} />
                  {indexCount} chunks from {indexCount} indexed — ready to answer your questions.
                </p>
                <div className="chat-suggestions">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} className="chat-suggestion" onClick={() => doSend(s)}>
                      <i className="fa-regular fa-lightbulb" style={{ marginRight: 6, fontSize: 12 }} />{s}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <h2>No documents indexed yet</h2>
                <p>Upload a PDF, paste a URL, or add raw text to the index before chatting. AutoDocThinker will answer from your documents.</p>
                <button className="btn btn-primary btn-lg" onClick={() => onNavigate?.('ingest')}>
                  <i className="fa-solid fa-cloud-arrow-up" /> Upload Documents
                </button>
                <div className="chat-suggestions" style={{ marginTop: 8 }}>
                  <span style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>Or try asking a general question — Wikipedia fallback is active</span>
                </div>
              </>
            )}
          </div>
        ) : (
          <>
            {messages.map((m, i) => (
              <MessageBubble key={i} role={m.role} content={m.content} sources={lastSources[m._idx]} />
            ))}
            {loading && <TypingIndicator />}
          </>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-area">
        {!hasDocuments && messages.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10, paddingLeft: 4 }}>
            <i className="fa-solid fa-triangle-exclamation" />
            No documents indexed — answers will use Wikipedia fallback only.
            <button style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: 12, fontWeight: 600, cursor: 'pointer', padding: 0 }}
              onClick={() => onNavigate?.('ingest')}>Upload now →</button>
          </div>
        )}
        <div className="chat-input-box">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..." rows={1} id="chat-input" />
          <button className="chat-send-btn" onClick={() => doSend(input)} disabled={loading || !input.trim()} id="btn-send">
            <i className="fa-solid fa-paper-plane" />
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, paddingLeft: 2 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            <kbd style={{ fontSize: 10, padding: '1px 5px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 4 }}>Enter</kbd> to send &nbsp;·&nbsp;
            <kbd style={{ fontSize: 10, padding: '1px 5px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 4 }}>Shift+Enter</kbd> new line
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {RAG_LABELS[ragMode]?.label} · {domainList.find((d) => d.name === domain)?.label}
          </span>
        </div>
      </div>
    </div>
  );
}
