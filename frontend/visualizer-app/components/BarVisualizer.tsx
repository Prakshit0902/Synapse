"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";

type AgentState = "idle" | "connecting" | "listening" | "thinking" | "speaking";
const BAR_COUNT = 5;

const STATE_CONFIG: Record<AgentState, { color: string; glow: string; label: string; profile: { min: number; max: number; speed: number }[] }> = {
  idle: {
    color: "#555",
    glow: "0 0 0px transparent",
    label: "Idle",
    profile: Array(5).fill({ min: 4, max: 8, speed: 3.0 }),
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

const STATE_ORDER: AgentState[] = ["idle", "connecting", "listening", "thinking", "speaking"];

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
      const next = profile.map((p, i) => {
        const s = Math.sin(t * Math.PI * 2 * (1 / p.speed) + phases[i]);
        return p.min + ((s + 1) / 2) * (p.max - p.min);
      });
      setHeights(next);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [state]);

  return heights;
}

function Bar({ height, color }: { height: number; color: string }) {
  return (
    <motion.div
      animate={{ height: `${height}px`, backgroundColor: color }}
      transition={{ height: { duration: 0.07, ease: "easeOut" }, backgroundColor: { duration: 0.5 } }}
      style={{ width: 14, borderRadius: 99, minHeight: 4, flexShrink: 0 }}
    />
  );
}

function StateBtn({ state, active, onClick }: { state: AgentState; active: boolean; onClick: () => void }) {
  const { color, label } = STATE_CONFIG[state];
  return (
    <motion.button
      onClick={onClick}
      whileTap={{ scale: 0.95 }}
      style={{
        padding: "7px 18px", borderRadius: 99,
        border: `1.5px solid ${active ? color : "#2a2a2a"}`,
        background: active ? color + "25" : "transparent",
        color: active ? color : "#555",
        fontSize: 13, fontFamily: "inherit", cursor: "pointer",
        transition: "all 0.3s", letterSpacing: "0.03em", outline: "none",
      }}
    >
      {label}
    </motion.button>
  );
}

export default function BarVisualizerDemo() {
  const [state, setState] = useState<AgentState>("idle");
  const heights = useBarHeights(state);
  const { color, glow, label } = STATE_CONFIG[state];

  // Naye States text dikhane ke liye
  const [userText, setUserText] = useState("");
  const [nainaText, setNainaText] = useState("");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {

    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    setState("connecting");

    wsRef.current.onopen = () => {
      console.log("Connected to Synapse Engine!");
      setState("idle");
    };


   wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // 🔍 DEBUG LOG: Python ne exact kya bheja?
        console.log("📥 Received from Python:", data);

        if (data.type === "state") {
          // Status check karo aur safe type casting karo
          const newStatus = data.status || data.state; // Backup just in case

          if (newStatus) {
            console.log("🔄 Updating UI State to:", newStatus);
            setState(newStatus as AgentState);
          }

          if (newStatus === "listening") {
              setUserText(""); // Clear previous conversation
              setNainaText("");
          }
        }
        else if (data.type === "user_text") {
          console.log("📝 Updating User Text:", data.text);
          setUserText(data.text);
        }
        else if (data.type === "naina_text") {
          console.log("🔊 Appending Naina Text:", data.text);
          setNainaText((prev) => prev + " " + data.text);
        }

      } catch (error) {
        console.error("WebSocket Message Error:", error);
      }
    };

    wsRef.current.onclose = () => {
      console.log("Disconnected from Synapse Engine");
      setState("idle");
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080808",
      color: "#eee",
      fontFamily: "'DM Mono', 'Fira Code', 'Courier New', monospace",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 48,
      padding: "60px 24px",
    }}>

      {}
      <div style={{ textAlign: "center", height: "80px", maxWidth: "600px" }}>
        <p style={{ color: "#06b6d4", fontSize: "16px", margin: "0 0 10px" }}>
            {userText && `You: "${userText}"`}
        </p>
        <p style={{ color: "#f97316", fontSize: "18px", margin: 0, fontWeight: "bold" }}>
            {nainaText && `Naina: ${nainaText}`}
        </p>
      </div>

      {}
      <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
        {/* Orbit rings */}
        {[1.7, 2.4, 3.2].map((scale, i) => (
          <motion.div
            key={i}
            animate={{ rotate: i % 2 === 0 ? 360 : -360, opacity: [0.04, 0.1, 0.04] }}
            transition={{ duration: 10 + i * 5, repeat: Infinity, ease: "linear" }}
            style={{
              position: "absolute",
              width: 160 * scale, height: 160 * scale,
              borderRadius: "50%",
              border: `1px solid ${color}`,
              transition: "border-color 0.5s",
            }}
          />
        ))}

    {/* Main box */}
        <motion.div
          animate={{ boxShadow: glow }}
          transition={{ duration: 0.6 }}
          style={{
            width: 160, height: 160,
            borderRadius: 28,
            background: "#0f0f0f",
            border: "1px solid #1e1e1e",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            position: "relative",
            zIndex: 1,
            overflow: "hidden" 
          }}
        >
          {}
          <motion.div
            animate={{ 
              color: color,
              textShadow: `0px 0px 12px ${color}80` 
            }}
            transition={{ duration: 0.5 }}
            style={{
              position: "absolute",
              top: 24, 
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: "0.4em",
              textTransform: "uppercase",
              zIndex: 0, 
              opacity: state === "idle" ? 0.3 : 0.9, 
            }}
          >
            Naina
          </motion.div>

          {}
          <div style={{ display: "flex", gap: 8, zIndex: 2 }}>
            {heights.map((h, i) => (
              <Bar key={i} height={h} color={color} />
            ))}
          </div>
        </motion.div>

        {/* Label */}
        <AnimatePresence mode="wait">
          <motion.p
            key={state}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            style={{
              position: "absolute",
              bottom: -42,
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
    </div>
  );
}