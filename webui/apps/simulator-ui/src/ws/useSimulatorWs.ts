import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { WsClientMessage, WsServerMessage } from "./types";

function wsUrl() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws`;
}

export function useSimulatorWs() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsServerMessage | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [sensorData, setSensorData] = useState<Record<string, unknown>>({});
  const [nlpLog, setNlpLog] = useState<Array<{ ts: number; direction: "in" | "out"; payload: unknown }>>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const backoffRef = useRef<number>(400);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const ws = new WebSocket(wsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      backoffRef.current = 400;
      // request initial status
      ws.send(JSON.stringify({ type: "get_status" } satisfies WsClientMessage));
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      // Reconnect with capped exponential backoff
      const wait = Math.min(8000, backoffRef.current);
      backoffRef.current = Math.min(8000, backoffRef.current * 1.7);
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      reconnectRef.current = window.setTimeout(() => connect(), wait);
    };

    ws.onerror = () => {
      // onclose will handle reconnect
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WsServerMessage;
        setLastMessage(msg);
        if ((msg as any)?.type === "status_update") setStatus(msg);
        if ((msg as any)?.type === "sensor_data") setSensorData((msg as any)?.sensors ?? {});
        if ((msg as any)?.type === "nlp_response") {
          setNlpLog((l) => [...l.slice(-199), { ts: Date.now(), direction: "in", payload: msg }]);
        }
      } catch {
        // ignore non-JSON
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((m: WsClientMessage) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify(m));
    return true;
  }, []);

  const sendNlpCommand = useCallback(
    (text: string) => {
      setNlpLog((l) => [...l.slice(-199), { ts: Date.now(), direction: "out", payload: { text } }]);
      return send({ type: "nlp_command", text } satisfies WsClientMessage);
    },
    [send]
  );

  const api = useMemo(
    () => ({
      connected,
      lastMessage,
      status,
      sensorData,
      nlpLog,
      subscribe: (sensors: string[]) => send({ type: "subscribe", sensors } satisfies WsClientMessage),
      unsubscribe: (sensors: string[]) => send({ type: "unsubscribe", sensors } satisfies WsClientMessage),
      getStatus: () => send({ type: "get_status" } satisfies WsClientMessage),
      setUpdateRate: (interval: number) => send({ type: "set_update_rate", interval } satisfies WsClientMessage),
      sendNlpCommand,
      startProtocol: (protocol: string) => sendNlpCommand(`start ${protocol}`),
      stopProtocol: (protocol: string) => sendNlpCommand(`stop ${protocol}`),
    }),
    [connected, lastMessage, nlpLog, send, sendNlpCommand, sensorData, status]
  );

  return api;
}

