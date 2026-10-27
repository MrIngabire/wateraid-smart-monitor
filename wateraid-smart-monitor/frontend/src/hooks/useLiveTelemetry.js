import { useEffect, useRef, useState } from 'react';

/**
 * WebSocket hook for real-time telemetry with polling fallback.
 * @param {string} wsUrl  - e.g. 'ws://localhost:8000/ws/telemetry/'
 * @param {function} onUpdate - callback invoked per message
 */
export function useLiveTelemetry(wsUrl, onUpdate) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const onUpdateRef = useRef(onUpdate);

  // Keep the latest callback without re-subscribing
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  useEffect(() => {
    let isUnmounted = false;

    const connect = () => {
      if (isUnmounted) return;
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          console.log('[WS] Connected');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (onUpdateRef.current) onUpdateRef.current(data);
          } catch (err) {
            console.warn('[WS] Bad message:', err);
          }
        };

        ws.onclose = () => {
          setConnected(false);
          console.log('[WS] Disconnected — reconnecting in 3s...');
          if (!isUnmounted) {
            reconnectTimer.current = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          // Silently close; onclose will trigger reconnection
          ws.close();
        };
      } catch (err) {
        console.warn('[WS] Connection failed:', err);
        if (!isUnmounted) {
          reconnectTimer.current = setTimeout(connect, 5000);
        }
      }
    };

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [wsUrl]);

  return { connected };
}