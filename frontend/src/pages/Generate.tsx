import { useState } from "react";
import { useApp } from "../store";

interface GenEvent {
  type: string;
  chapter?: number;
  chapter_title?: string;
  current_segment?: number;
  total_segments?: number;
  text_preview?: string;
  duration_ms?: number;
  output_path?: string;
  total_duration_ms?: number;
  message?: string;
}

function formatDuration(ms: number): string {
  const sec = Math.floor(ms / 1000);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}小时${m}分`;
  if (m > 0) return `${m}分${s}秒`;
  return `${s}秒`;
}

export default function Generate() {
  const { bookTitle, bookAuthor, chapters, roles, engineConfigs, outputFormat, setOutputFormat } = useApp();
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<GenEvent[]>([]);
  const [outputPath, setOutputPath] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (chapters.length === 0) {
      setError("请先导入小说");
      return;
    }

    setRunning(true);
    setError("");
    setEvents([]);
    setOutputPath("");

    const ws = new WebSocket(`ws://${location.host}/api/generate/run/gen1`);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          title: bookTitle || "未命名有声书",
          author: bookAuthor,
          chapters: chapters.map((c) => ({
            index: c.index,
            title: c.title,
            sml: c.sml || `[voice:旁白]${c.text}[/voice]`,
          })),
          voices: roles.map((r) => ({
            name: r.name,
            engine: r.voice?.engine || "edge",
            voice_id: r.voice?.voice_id || "",
            reference_audio: r.voice?.reference_audio,
            pitch: r.voice?.pitch || 0,
            speed: r.voice?.speed || 1,
          })),
          engine_configs: engineConfigs,
          output_format: outputFormat,
        })
      );
    };

    ws.onmessage = (ev) => {
      const data: GenEvent = JSON.parse(ev.data);
      setEvents((prev) => [...prev, data]);

      if (data.type === "generation_done") {
        setOutputPath(data.output_path || "");
      }
      if (data.type === "error") {
        setError(data.message || "未知错误");
      }
    };

    ws.onerror = () => setError("WebSocket 连接错误");
    ws.onclose = () => setRunning(false);
  };

  const completedChapters = events.filter((e) => e.type === "chapter_done").length;
  const totalDuration = events.find((e) => e.type === "generation_done")?.total_duration_ms || 0;

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>生成有声书</h1>

      <div style={{ background: "#fff", borderRadius: 8, padding: 20, marginBottom: 20 }}>
        <p style={{ marginTop: 0 }}>书名：{bookTitle || "未命名"}</p>
        <p>章节数：{chapters.length}</p>
        <p>角色数：{roles.length}</p>

        <label style={{ marginRight: 12 }}>
          输出格式：
          <select value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)} style={{ padding: "4px 8px", marginLeft: 4 }}>
            <option value="m4b">M4B（推荐）</option>
            <option value="mp3">MP3</option>
            <option value="wav">WAV</option>
          </select>
        </label>

        <div style={{ marginTop: 16 }}>
          <button
            onClick={handleGenerate}
            disabled={running}
            style={{
              padding: "12px 40px",
              background: running ? "#ccc" : "#ff7043",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: running ? "not-allowed" : "pointer",
              fontSize: 18,
            }}
          >
            {running ? "生成中..." : "🎬 开始生成"}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: 12, background: "#fee", borderRadius: 8, color: "#c00", marginBottom: 16 }}>
          {error}
        </div>
      )}

      {running && chapters.length > 0 && (
        <div style={{ background: "#fff", borderRadius: 8, padding: 20, marginBottom: 16 }}>
          <div style={{ background: "#e0e0e0", borderRadius: 4, height: 24, overflow: "hidden" }}>
            <div
              style={{
                width: `${(completedChapters / chapters.length) * 100}%`,
                background: "#4caf50",
                height: "100%",
                transition: "width 0.3s",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 13,
              }}
            >
              {completedChapters} / {chapters.length} 章
            </div>
          </div>
        </div>
      )}

      {events.length > 0 && (
        <div style={{ background: "#fff", borderRadius: 8, padding: 20, marginBottom: 16 }}>
          <h3 style={{ marginTop: 0 }}>日志</h3>
          <div style={{ maxHeight: 300, overflowY: "auto", fontFamily: "monospace", fontSize: 12 }}>
            {events.slice(-50).map((ev, i) => (
              <div key={i} style={{ padding: "1px 0", color: ev.type.includes("error") ? "#c00" : ev.type.includes("done") ? "#080" : "#666" }}>
                [{ev.type}] {ev.chapter_title || ""} {ev.current_segment !== undefined ? `(${ev.current_segment}/${ev.total_segments})` : ""}
                {ev.duration_ms ? ` → ${formatDuration(ev.duration_ms)}` : ""}
              </div>
            ))}
          </div>
        </div>
      )}

      {outputPath && (
        <div style={{ background: "#c8e6c9", borderRadius: 8, padding: 20 }}>
          <h3 style={{ marginTop: 0, color: "#1b5e20" }}>{"✅ 生成完成！"}</h3>
          <p>总时长：{formatDuration(totalDuration)}</p>
          <p>输出文件：<code>{outputPath}</code></p>
        </div>
      )}
    </div>
  );
}
