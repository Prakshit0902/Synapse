"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";

type AgentState =
  | "idle"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking";

const BAR_COUNT = 5;

const STATE_CONFIG: Record<
  AgentState,
  {
    color: string;
    glow: string;
    label: string;
    profile: { min: number; max: number; speed: number }[];
  }
> = {
  idle: {
    color: "#555",
    glow: "0 0 0px transparent",
    label: "Idle",
    profile: Array(5).fill({
      min: 4,
      max: 8,
      speed: 3.0,
    }),
  },
  connecting: {
    color: "#6366f1",
    glow: "0 0 40px rgba(99,102,241,0.5)",
    label: "Connecting…",
    profile: [
      { min: 6, max: 30, speed: 0.55 },
      { min: 6, max: 50, speed: 0.45 },
      { min: 6, max: 65, speed: 0.4 },
      { min: 6, max: 50, speed: 0.45 },
      { min: 6, max: 30, speed: 0.55 },
    ],
  },
  listening: {
    color: "#06b6d4",
    glow: "0 0 40px rgba(6,182,212,0.5)",
    label: "Listening",
    profile: [
      { min: 8, max: 22, speed: 1.3 },
      { min: 8, max: 32, speed: 1.5 },
      { min: 8, max: 18, speed: 1.1 },
      { min: 8, max: 28, speed: 1.4 },
      { min: 8, max: 20, speed: 1.2 },
    ],
  },
  thinking: {
    color: "#a855f7",
    glow: "0 0 40px rgba(168,85,247,0.5)",
    label: "Thinking…",
    profile: [
      { min: 10, max: 40, speed: 0.85 },
      { min: 10, max: 60, speed: 1.0 },
      { min: 10, max: 70, speed: 0.75 },
      { min: 10, max: 60, speed: 0.95 },
      { min: 10, max: 40, speed: 0.9 },
    ],
  },
  speaking: {
    color: "#f97316",
    glow: "0 0 40px rgba(249,115,22,0.6)",
    label: "Speaking",
    profile: [
      { min: 12, max: 55, speed: 0.38 },
      { min: 12, max: 72, speed: 0.33 },
      { min: 12, max: 82, speed: 0.3 },
      { min: 12, max: 72, speed: 0.33 },
      { min: 12, max: 55, speed: 0.38 },
    ],
  },
};

function useBarHeights(state: AgentState) {
  const [heights, setHeights] = useState<number[]>(Array(BAR_COUNT).fill(8));
  const rafRef = useRef<number>(0);
  const startRef = useRef<number>(Date.now());

  useEffect(() => {
    startRef.current = Date.now();
    const phases = [0, 0.6, 1.2, 1.8, 2.4];
    const tick = () => {
      const t = (Date.now() - startRef.current) / 1000;
      const { profile } = STATE_CONFIG[state];
      setHeights(
        profile.map((p, i) => {
          const s = Math.sin(t * Math.PI * 2 * (1 / p.speed) + phases[i]);
          return p.min + ((s + 1) / 2) * (p.max - p.min);
        })
      );
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [state]);

  return heights;
}

function Bar({ height, color }: { height: number; color: string; }) {
  return (
    <motion.div
      animate={{ height: `${height}px`, backgroundColor: color }}
      transition={{ height: { duration: 0.07, ease: "easeOut" }, backgroundColor: { duration: 0.5 } }}
      style={{ width: 14, borderRadius: 999, minHeight: 4, flexShrink: 0 }}
    />
  );
}

interface TextLine {
  id: number;
  text: string;
}
const MAX_CHARS_PER_LINE = 38;
const MAX_LINES = 2;

export default function BarVisualizerDemo() {
  const [state, setState] = useState<AgentState>("idle");
  const heights = useBarHeights(state);
  const { color, glow, label } = STATE_CONFIG[state];

  const [userText, setUserText] = useState("");
  const [lines, setLines] = useState<TextLine[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const lineIdRef = useRef(0);
  const textBufferRef = useRef("");

  // Naye UI Popup States
  const [toastMsg, setToastMsg] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  // ─────────────────────────────────────────
  // IPC RECEIVER FOR ELECTRON (DOWNLOAD TOAST)
  // ─────────────────────────────────────────
  useEffect(() => {
    if (typeof window !== "undefined" && (window as any).require) {
      const { ipcRenderer } = (window as any).require("electron");

      const handleBackendStatus = (event: any, msg: string) => {
        setToastMsg(msg);
        if (msg.includes("Downloading")) {
          setIsDownloading(true);
        } else if (msg.includes("Complete")) {
          setIsDownloading(false);
          // 4 seconds baad toast hata do
          setTimeout(() => setToastMsg(""), 4000);
        }
      };

      ipcRenderer.on("backend-status", handleBackendStatus);
      return () => {
        ipcRenderer.removeAllListeners("backend-status");
      };
    }
  }, []);

  // ─────────────────────────────────────────
  // FLUSH BUFFER
  // ─────────────────────────────────────────
  const flushBuffer = (force = false) => {
    const text = textBufferRef.current.trim();
    if (!text) return;
    if (!force && text.length < MAX_CHARS_PER_LINE) return;

    textBufferRef.current = "";
    const id = lineIdRef.current++;
    setLines((prev) => {
      const next = [...prev, { id, text }];
      return next.slice(-MAX_LINES);
    });
  };

  useEffect(() => {
    const timer = setInterval(() => flushBuffer(false), 450);
    return () => clearInterval(timer);
  }, []);

  // ─────────────────────────────────────────
  // WEBSOCKET
  // ─────────────────────────────────────────
  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;
    let isMounted = true;

    function connect() {
      if (!isMounted) return;
      wsRef.current = new WebSocket("ws://localhost:8000/ws");
      setState("connecting");

      wsRef.current.onopen = () => setState("idle");

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "state") {
            const s = data.status || data.state;
            if (!s) return;
            setState(s as AgentState);
            if (s === "listening") {
              textBufferRef.current = "";
              setUserText("");
              setLines([]);
            }
            if (s === "idle") {
              flushBuffer(true);
            }
          } else if (data.type === "user_text") {
            setUserText(data.text);
          } else if (data.type === "naina_text") {
            textBufferRef.current += ` ${data.text}`;
            if (textBufferRef.current.length >= MAX_CHARS_PER_LINE) {
              flushBuffer(false);
            }
          }
        } catch (e) {
          console.error(e);
        }
      };

      wsRef.current.onerror = () => wsRef.current?.close();

      wsRef.current.onclose = () => {
        if (isMounted) reconnectTimer = setTimeout(connect, 2000);
      };
    }

    connect();
    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#050505",
        color: "#eee",
        fontFamily: "'DM Mono','Fira Code','Courier New',monospace",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* ───────────────────────────────────── */}
      {/* TEXT ZONE (No changes here) */}
      {/* ───────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: "calc(50vh + 140px)",
          left: "50%",
          transform: "translateX(-50%)",
          width: "min(760px, 88vw)",
          height: 170,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          alignItems: "center",
          padding: "0 18px",
          pointerEvents: "none",
          backdropFilter: "blur(8px)",
          WebkitMaskImage: "linear-gradient(to top, transparent 0%, rgba(0,0,0,0.8) 18%, black 38%, black 100%)",
          maskImage: "linear-gradient(to top, transparent 0%, rgba(0,0,0,0.8) 18%, black 38%, black 100%)",
        }}
      >
        <AnimatePresence mode="wait">
          {userText && (
            <motion.p
              key="user"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 0.72, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3 }}
              style={{
                color: "#06b6d4",
                fontSize: 14,
                margin: "0 0 12px",
                textAlign: "center",
                letterSpacing: "0.02em",
                maxWidth: "100%",
              }}
            >
              &ldquo;{userText}&rdquo;
            </motion.p>
          )}
        </AnimatePresence>

        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: 10,
          }}
        >
          <AnimatePresence initial={false}>
            {lines.map((line, index) => {
              const isLatest = index === lines.length - 1;
              return (
                <motion.p
                  layout
                  key={line.id}
                  initial={{ opacity: 0, y: 26, filter: "blur(10px)" }}
                  animate={{
                    opacity: isLatest ? 1 : 0.22,
                    y: 0,
                    filter: "blur(0px)",
                    scale: isLatest ? 1 : 0.96,
                  }}
                  exit={{ opacity: 0, y: -40, filter: "blur(12px)" }}
                  transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                  style={{
                    color: "#f97316",
                    fontSize: 17,
                    margin: 0,
                    fontWeight: 500,
                    lineHeight: 1.55,
                    letterSpacing: "0.02em",
                    textAlign: "center",
                    width: "100%",
                    textShadow: "0 0 22px rgba(249,115,22,0.22)",
                    willChange: "transform, opacity, filter",
                  }}
                >
                  {line.text}
                </motion.p>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* ───────────────────────────────────── */}
      {/* CENTER BOX (No changes here) */}
      {/* ───────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {[1.7, 2.4, 3.2].map((scale, i) => (
          <motion.div
            key={i}
            animate={{
              rotate: i % 2 === 0 ? 360 : -360,
              opacity: [0.04, 0.1, 0.04],
            }}
            transition={{ duration: 10 + i * 5, repeat: Infinity, ease: "linear" }}
            style={{
              position: "absolute",
              width: 160 * scale,
              height: 160 * scale,
              borderRadius: "50%",
              border: `1px solid ${color}`,
              transition: "border-color 0.5s",
              pointerEvents: "none",
            }}
          />
        ))}

        <motion.div
          animate={{ boxShadow: glow }}
          transition={{ duration: 0.6 }}
          style={{
            width: 160,
            height: 160,
            borderRadius: 28,
            background: "#0d0d0d",
            border: "1px solid #1d1d1d",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <motion.div
            animate={{ color: color, textShadow: `0 0 12px ${color}80` }}
            transition={{ duration: 0.5 }}
            style={{
              position: "absolute",
              top: 22,
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.45em",
              textTransform: "uppercase",
              opacity: state === "idle" ? 0.3 : 0.85,
              transition: "opacity 0.4s",
            }}
          >
            Naina
          </motion.div>

          <div style={{ display: "flex", gap: 8 }}>
            {heights.map((h, i) => (
              <Bar key={i} height={h} color={color} />
            ))}
          </div>
        </motion.div>

        <AnimatePresence mode="wait">
          <motion.p
            key={state}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            style={{
              position: "absolute",
              top: "calc(100% + 20px)",
              left: "50%",
              transform: "translateX(-50%)",
              fontSize: 11,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color,
              whiteSpace: "nowrap",
              margin: 0,
            }}
          >
            {label}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* ───────────────────────────────────── */}
      {/* 🍎 APPLE STYLE DOWNLOADING TOAST */}
      {/* ───────────────────────────────────── */}
      <AnimatePresence>
        {toastMsg && (
          <motion.div
            initial={{ opacity: 0, x: 100, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.9 }}
            transition={{ type: "spring", bounce: 0.3, duration: 0.6 }}
            style={{
              position: "fixed",
              bottom: "40px",
              right: "40px",
              background: "rgba(20, 20, 20, 0.85)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.08)",
              padding: "16px 24px",
              borderRadius: "20px",
              display: "flex",
              alignItems: "center",
              gap: "16px",
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
              zIndex: 9999,
            }}
          >
            {isDownloading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                style={{
                  width: "18px",
                  height: "18px",
                  borderRadius: "50%",
                  border: "2px solid rgba(255,255,255,0.1)",
                  borderTopColor: "#06b6d4",
                }}
              />
            ) : (
              <div style={{ color: "#10b981", fontSize: "18px", fontWeight: "bold" }}>✓</div>
            )}
            <span style={{
              color: "#eee",
              fontSize: "14px",
              fontWeight: 500,
              letterSpacing: "0.02em",
              fontFamily: "system-ui, -apple-system, sans-serif"
            }}>
              {toastMsg}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}