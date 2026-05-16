const BASE = '';

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Health
export const getHealth = () => request('/health');

// Domains
export const getDomains = () => request('/domains');
export const getDomain = (name) => request(`/domains/${name}`);

// RAG
export const getRagModes = () => request('/rag-modes');
export const getRagProfiles = () => request('/rag-profiles');
export const queryRag = (payload) =>
  request('/rag/query', { method: 'POST', body: JSON.stringify(payload) });

// Chat Sessions
export const createSession = () =>
  request('/chat/sessions', { method: 'POST' });
export const getSession = (id) => request(`/chat/sessions/${id}`);
export const selectProfile = (id, payload) =>
  request(`/chat/sessions/${id}/select-profile`, { method: 'POST', body: JSON.stringify(payload) });
export const sendMessage = (id, payload) =>
  request(`/chat/sessions/${id}/messages`, { method: 'POST', body: JSON.stringify(payload) });

// Ingestion
export const ingestSource = (payload) =>
  request('/ingest/source', { method: 'POST', body: JSON.stringify(payload) });

export const ingestUpload = async (formData) => {
  const res = await fetch('/ingest/upload', { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

export const ingestText = (payload) =>
  request('/ingest/text', { method: 'POST', body: JSON.stringify(payload) });

export const autoIngest = () =>
  request('/ingest/auto', { method: 'POST' });

// Index
export const getIndexStatus = () => request('/index/status');
export const removeSource = (sourceId) => request(`/index/source/${sourceId}`, { method: 'DELETE' });
export const clearIndex = () => request('/index', { method: 'DELETE' });

// Admin
export const getAdminSummary = () => request('/admin/summary');
