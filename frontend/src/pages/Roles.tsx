import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp, type RoleData } from "../store";

interface ProgressEvent {
  type: string;
  chapter?: number;
  total?: number;
  sml_preview?: string;
  roles_found?: string[];
}

export default function Roles() {
  const { chapters, setRoles, llmConfig } = useApp();
  const navigate = useNavigate();
  const [mode, setMode] = useState("single_pass");
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [resultRoles, setResultRoles] = useState<RoleData[]>([]);
  const [error, setError] = useState("");

  const handleStart = async () => {
    if (!llmConfig.api_key) {
      setError("请先在设置页配置 LLM API Key");
      return;
    }
    if (chapters.length === 0) {
      setError("请先导入小说");
      return;
    }

    setRunning(true);
    setError("");
    setEvents([]);

    const ws = new WebSocket(`ws://${location.host}/api/roles/stream/job1`);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          provider: llmConfig.provider,
          base_url: llmConfig.base_url,
          api_key: llmConfig.api_key,
          model: llmConfig.model,
          temperature: llmConfig.temperature,
          mode,
          chapters: chapters.map((c) => ({ index: c.index, title: c.title, text: c.text })),
        })
      );
    };

    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      setEvents((prev) => [...prev, data]);

      if (data.type === "pipeline_done" && data.roles) {
        const newRoles: RoleData[] = data.roles.map((r: any) => ({
          name: r.name,
          gender: r.gender,
          age: r.age,
          aliases: r.aliases || [],
        }));
        setResultRoles(newRoles);
        setRoles(newRoles);
      }
    };

    ws.onerror = () => setError("WebSocket 连接错误");
    ws.onclose = () => setRunning(false);
  };

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>角色识别</h1>

      {chapters.length === 0 ? (
        <div style={{ padding: 20, background: "#fff3cd", borderRadius: 8 }}>
          请先导入小说 → <a href="#/">去导入</a>
        </div>
      ) : (
        <>
          <div style={{ background: "#fff", borderRadius: 8, padding: 20, marginBottom: 20 }}>
            <p style={{ marginTop: 0 }}>共 {chapters.length} 章</p>

            <label style={{ marginRight: 20 }}>
              <input type="radio" value="single_pass" checked={mode === "single_pass"} onChange={(e) => setMode(e.target.value)} />
              {" "}单轮模式（快速，成本低）
            </label>
            <label>
              <input type="radio" value="two_pass" checked={mode === "two_pass"} onChange={(e) => setMode(e.target.value)} />
              {" "}两阶段模式（精度高，成本约 2 倍）
            </label>

            <div style={{ marginTop: 16 }}>
              <button
                onClick={handleStart}
                disabled={running}
                style={{
                  padding: "10px 30px",
                  background: running ? "#ccc" : "#4fc3f7",
                  color: "#fff",
                  border: "none",
                  borderRadius: 6,
                  cursor: running ? "not-allowed" : "pointer",
                  fontSize: 16,
                }}
              >
                {running ? "识别中..." : "开始识别"}
              </button>
            </div>
          </div>

          {error && (
            <div style={{ padding: 12, background: "#fee", borderRadius: 8, color: "#c00", marginBottom: 16 }}>
              {error}
            </div>
          )}

          {events.length > 0 && (
            <div style={{ background: "#fff", borderRadius: 8, padding: 20, marginBottom: 20 }}>
              <h3 style={{ marginTop: 0 }}>进度</h3>
              <div style={{ maxHeight: 300, overflowY: "auto", fontFamily: "monospace", fontSize: 13 }}>
                {events.map((ev, i) => (
                  <div key={i} style={{ padding: "2px 0", color: ev.type.includes("error") ? "#c00" : ev.type.includes("done") ? "#080" : "#666" }}>
                    [{ev.type}] {ev.chapter !== undefined ? `第${ev.chapter + 1}章` : ""} {ev.total !== undefined ? `/${ev.total}` : ""}
                    {ev.sml_preview ? ` → ${ev.sml_preview.slice(0, 60)}...` : ""}
                  </div>
                ))}
              </div>
            </div>
          )}

          {resultRoles.length > 0 && (
            <div style={{ background: "#fff", borderRadius: 8, padding: 20 }}>
              <h3 style={{ marginTop: 0 }}>识别到 {resultRoles.length} 个角色</h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
                    <th style={{ padding: 8 }}>角色名</th>
                    <th style={{ padding: 8 }}>性别</th>
                    <th style={{ padding: 8 }}>年龄</th>
                    <th style={{ padding: 8 }}>别名</th>
                  </tr>
                </thead>
                <tbody>
                  {resultRoles.map((r, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: 8 }}>{r.name}</td>
                      <td style={{ padding: 8 }}>
                        {r.gender === "male" ? "男" : r.gender === "female" ? "女" : "未知"}
                      </td>
                      <td style={{ padding: 8 }}>
                        {{ child: "儿童", teen: "少年", adult: "成年", elder: "老年" }[r.age] || "未知"}
                      </td>
                      <td style={{ padding: 8, color: "#999" }}>{r.aliases.join("、")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <button
                onClick={() => navigate("/voices")}
                style={{ marginTop: 16, padding: "10px 30px", background: "#4caf50", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 16 }}
              >
                分配音色 →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
