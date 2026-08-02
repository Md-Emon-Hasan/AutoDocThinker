const BASE = '';
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN;

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(ADMIN_TOKEN ? { 'X-Admin-Token': ADMIN_TOKEN } : {}),
      ...options.headers,
    },
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

// -- Streaming (SSE) ---------------------------------------------------
//
// Approach: fetch() + ReadableStream with manual SSE frame parsing, not
// EventSource + a job-id GET endpoint. EventSource cannot send a POST
// body, and a RAG query needs one (question, domain, mode, scope...);
// routing through a job-creation POST plus a polling GET would need a
// server-side job store purely to work around that limitation. This
// needs no job store and keeps the request shape identical to the
// non-streaming endpoints. See backend/app/api/stream_routes.py for the
// server side of this same decision.

/** Parse one SSE frame (the text between two blank lines) into
 * {event, data}, or null for a keepalive/empty frame. */
export function parseSSEFrame(frame) {
  let eventType = 'message';
  const dataLines = [];
  for (const line of frame.split('\n')) {
    if (!line || line.startsWith(':')) continue; // keepalive comment
    if (line.startsWith('event: ')) eventType = line.slice(7);
    else if (line.startsWith('data: ')) dataLines.push(line.slice(6));
  }
  if (dataLines.length === 0) return null;
  try {
    return { event: eventType, data: JSON.parse(dataLines.join('\n')) };
  } catch {
    return null;
  }
}

/** POST `payload` to `url`, calling onEvent(...) for each parsed SSE
 * event as it arrives. Pass `signal` (from an AbortController) to
 * support cancellation -- aborting the fetch closes the underlying
 * connection, which the backend detects as a disconnect and uses to
 * stop the workflow (see stream_routes.py's request.is_disconnected()). */
export async function streamSSE(url, payload, { onEvent, signal } = {}) {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let frameEnd;
    while ((frameEnd = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, frameEnd);
      buffer = buffer.slice(frameEnd + 2);
      const parsed = parseSSEFrame(frame);
      if (parsed) onEvent(parsed);
    }
  }
}

/** Standalone streaming query (mirrors queryRag's payload shape). */
export const streamRagQuery = (payload, opts) =>
  streamSSE('/rag/stream', payload, opts);

/** Session-scoped streaming message (mirrors sendMessage's payload
 * shape); persists session history server-side same as sendMessage. */
export const streamChatMessage = (sessionId, payload, opts) =>
  streamSSE(`/chat/sessions/${sessionId}/messages/stream`, payload, opts);
