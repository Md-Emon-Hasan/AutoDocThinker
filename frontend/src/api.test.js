import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { parseSSEFrame, streamSSE, streamRagQuery, streamChatMessage } from './api';

describe('parseSSEFrame', () => {
  it('parses a well-formed event/data frame', () => {
    const frame = 'event: token\ndata: {"text":"hello"}';
    expect(parseSSEFrame(frame)).toEqual({ event: 'token', data: { text: 'hello' } });
  });

  it('ignores keepalive comment lines', () => {
    expect(parseSSEFrame(': keepalive')).toBeNull();
  });

  it('returns null for a frame with no data line', () => {
    expect(parseSSEFrame('event: token')).toBeNull();
  });

  it('returns null for malformed JSON in the data line', () => {
    expect(parseSSEFrame('event: token\ndata: not json')).toBeNull();
  });

  it('defaults event type to "message" when absent', () => {
    const parsed = parseSSEFrame('data: {"x":1}');
    expect(parsed.event).toBe('message');
  });

  it('joins multiple data lines before parsing', () => {
    const frame = 'event: done\ndata: {"a":1,\ndata: "b":2}';
    expect(parseSSEFrame(frame)).toEqual({ event: 'done', data: { a: 1, b: 2 } });
  });
});

function fakeStreamResponse(chunks, { ok = true, status = 200 } = {}) {
  let i = 0;
  const encoder = new TextEncoder();
  return {
    ok,
    status,
    body: {
      getReader() {
        return {
          async read() {
            if (i >= chunks.length) return { done: true, value: undefined };
            const value = encoder.encode(chunks[i]);
            i += 1;
            return { done: false, value };
          },
        };
      },
    },
    json: async () => ({ detail: 'error' }),
  };
}

describe('streamSSE', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls onEvent for each frame as it arrives, across chunk boundaries', async () => {
    global.fetch.mockResolvedValue(
      fakeStreamResponse([
        'event: node_start\ndata: {"node":"a"}\n\n',
        'event: token\ndata: {"text":"hi"}\n\nevent: done\ndata: {"response":{}}\n\n',
      ])
    );

    const events = [];
    await streamSSE('/rag/stream', { question: 'q' }, { onEvent: (e) => events.push(e) });

    expect(events.map((e) => e.event)).toEqual(['node_start', 'token', 'done']);
  });

  it('skips keepalive comments without invoking onEvent', async () => {
    global.fetch.mockResolvedValue(
      fakeStreamResponse([': keepalive\n\nevent: done\ndata: {"response":{}}\n\n'])
    );
    const events = [];
    await streamSSE('/rag/stream', {}, { onEvent: (e) => events.push(e) });
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe('done');
  });

  it('throws with the server-provided detail on a non-ok response', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 422,
      body: null,
      json: async () => ({ detail: 'bad request' }),
    });
    await expect(
      streamSSE('/rag/stream', {}, { onEvent: () => {} })
    ).rejects.toThrow('bad request');
  });

  it('passes the abort signal through to fetch', async () => {
    global.fetch.mockResolvedValue(fakeStreamResponse(['event: done\ndata: {}\n\n']));
    const controller = new AbortController();
    await streamSSE('/rag/stream', {}, { onEvent: () => {}, signal: controller.signal });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ signal: controller.signal })
    );
  });

  it('propagates an AbortError when the signal is already aborted', async () => {
    const controller = new AbortController();
    controller.abort();
    global.fetch.mockImplementation(() => {
      const err = new DOMException('The user aborted a request.', 'AbortError');
      return Promise.reject(err);
    });
    await expect(
      streamSSE('/rag/stream', {}, { onEvent: () => {}, signal: controller.signal })
    ).rejects.toThrow(/aborted/i);
  });
});

describe('streamRagQuery and streamChatMessage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('streamRagQuery posts to /rag/stream', async () => {
    global.fetch.mockResolvedValue(fakeStreamResponse(['event: done\ndata: {}\n\n']));
    await streamRagQuery({ question: 'q', domain: 'general', rag_mode: 'naive' }, { onEvent: () => {} });
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/rag/stream');
    expect(options.method).toBe('POST');
  });

  it('streamChatMessage posts to the session-scoped endpoint', async () => {
    global.fetch.mockResolvedValue(fakeStreamResponse(['event: done\ndata: {}\n\n']));
    await streamChatMessage('abc123', { message: 'hi' }, { onEvent: () => {} });
    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain('/chat/sessions/abc123/messages/stream');
  });
});
