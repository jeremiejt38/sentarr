import { useCallback, useEffect, useRef, useState } from 'react';

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`;

export const REFRESH_EVENT = 'sentarr:refresh';
export const TOAST_EVENT = 'sentarr:toast';

export type WsStatus = 'connected' | 'reconnecting' | 'offline';

const INITIAL_DELAY_MS = 1000;
const MAX_DELAY_MS = 30000;
const JITTER = 0.2;

const KNOWN_TYPES = new Set(['task_update', 'summary_update', 'new_alert']);

type WsMessage = { type?: unknown; [key: string]: unknown };

function isKnownMessage(msg: WsMessage): boolean {
  return typeof msg?.type === 'string' && KNOWN_TYPES.has(msg.type);
}

let unknownCount = 0;
export function getUnknownMessageCount() {
  return unknownCount;
}

export function useWebSocket<T = WsMessage>(onMessage?: (message: T) => void) {
  const [status, setStatus] = useState<WsStatus>('reconnecting');
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    let attempts = 0;
    let reconnectTimer: number | undefined;
    let closed = false;

    const schedule = () => {
      const base = Math.min(MAX_DELAY_MS, INITIAL_DELAY_MS * 2 ** attempts);
      const delay = base * (1 + (Math.random() * 2 - 1) * JITTER);
      reconnectTimer = window.setTimeout(open, delay);
    };

    const open = () => {
      if (closed) return;
      setStatus(attempts > 0 ? 'reconnecting' : 'reconnecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        const wasReconnect = attempts > 0;
        attempts = 0;
        setStatus('connected');
        if (wasReconnect) {
          window.dispatchEvent(new CustomEvent(REFRESH_EVENT, { detail: { type: 'resync' } }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WsMessage;
          if (isKnownMessage(data)) {
            onMessageRef.current?.(data as T);
          } else {
            unknownCount += 1;
          }
        } catch {
          unknownCount += 1;
        }
      };

      ws.onclose = () => {
        if (closed) return;
        wsRef.current = null;
        if (!navigator.onLine) {
          setStatus('offline');
        } else {
          setStatus('reconnecting');
        }
        attempts += 1;
        schedule();
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    const onVisibility = () => {
      if (!closed && document.visibilityState === 'visible' && wsRef.current?.readyState !== WebSocket.OPEN) {
        window.clearTimeout(reconnectTimer);
        open();
      }
    };
    const onOnline = () => {
      if (!closed && wsRef.current?.readyState !== WebSocket.OPEN) {
        window.clearTimeout(reconnectTimer);
        open();
      }
    };
    const onOffline = () => setStatus('offline');

    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);

    open();

    return () => {
      closed = true;
      window.clearTimeout(reconnectTimer);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  useEffect(() => connect(), [connect]);

  const send = useCallback(() => {
    // Lecture seule : le client n'envoie aucun message (WS-06).
  }, []);

  return { status, connected: status === 'connected', send };
}

export function useRefreshOnWebSocket(callback: () => void) {
  useEffect(() => {
    const handler = () => callback();
    window.addEventListener(REFRESH_EVENT, handler);
    return () => window.removeEventListener(REFRESH_EVENT, handler);
  }, [callback]);
}

export function emitToast(detail: { title: string; body?: string }) {
  window.dispatchEvent(new CustomEvent(TOAST_EVENT, { detail }));
}
