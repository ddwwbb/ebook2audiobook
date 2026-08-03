import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp, type VoiceAssignment } from "../store";

interface EngineInfo {
  id: string;
  name: string;
  type: string;
  cloning: boolean;
  license: string;
}

export default function Voices() {
  const { roles, setRoles } = useApp();
  const navigate = useNavigate();
  const [engines, setEngines] = useState<EngineInfo[]>([]);

  useEffect(() => {
    fetch("/api/voices/engines")
      .then((r) => r.json())
      .then((data) => setEngines(data.engines || []))
      .catch(() => {});
  }, []);

  const updateVoice = (roleName: string, voice: VoiceAssignment) => {
    setRoles(
      roles.map((r) =>
        r.name === roleName ? { ...r, voice } : r
      )
    );
  };

  const genderLabel = (g: string) =>
    g === "male" ? "男" : g === "female" ? "女" : "未知";

  const suggestEngine = (gender: string): VoiceAssignment => {
    if (gender === "male") return { engine: "edge", voice_id: "male_yunxi", speed: 1.0, pitch: 0 };
    if (gender === "female") return { engine: "edge", voice_id: "female_xiaoyi", speed: 1.0, pitch: 0 };
    return { engine: "edge", voice_id: "female_xiaoxiao", speed: 1.0, pitch: 0 };
  };

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>音色分配</h1>

      {roles.length === 0 ? (
        <div style={{ padding: 20, background: "#fff3cd", borderRadius: 8 }}>
          请先完成角色识别 → <a href="#/roles">去识别</a>
        </div>
      ) : (
        <>
          <div style={{ background: "#fff", borderRadius: 8, padding: 20 }}>
            <p style={{ color: "#666" }}>为每个角色选择 TTS 引擎和音色。默认使用 Edge TTS（免费）。</p>

            {roles.map((role, i) => {
              const current = role.voice || suggestEngine(role.gender);
              return (
                <div key={i} style={{ marginBottom: 16, padding: 16, borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                    <strong style={{ fontSize: 16 }}>{role.name}</strong>
                    <span style={{ color: "#999" }}>{genderLabel(role.gender)}</span>
                    {role.aliases.length > 0 && (
                      <span style={{ color: "#aaa", fontSize: 13 }}>（{role.aliases.join("、")}）</span>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <select
                      value={current.engine}
                      onChange={(e) =>
                        updateVoice(role.name, { ...current, engine: e.target.value, voice_id: "" })
                      }
                      style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc" }}
                    >
                      {engines.map((eng) => (
                        <option key={eng.id} value={eng.id}>
                          {eng.name} {eng.cloning ? "🎭" : ""} [{eng.license}]
                        </option>
                      ))}
                    </select>

                    <input
                      placeholder="voice_id / 音色名"
                      value={current.voice_id}
                      onChange={(e) => updateVoice(role.name, { ...current, voice_id: e.target.value })}
                      style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc", width: 200 }}
                    />

                    {engines.find((e) => e.id === current.engine)?.cloning && (
                      <input
                        placeholder="参考音频路径（克隆用）"
                        value={current.reference_audio || ""}
                        onChange={(e) =>
                          updateVoice(role.name, { ...current, reference_audio: e.target.value })
                        }
                        style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc", width: 250 }}
                      />
                    )}

                    <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      语速
                      <input
                        type="number"
                        step="0.1"
                        min="0.5"
                        max="2"
                        value={current.speed ?? 1.0}
                        onChange={(e) => updateVoice(role.name, { ...current, speed: parseFloat(e.target.value) })}
                        style={{ width: 60, padding: "4px", borderRadius: 4, border: "1px solid #ccc" }}
                      />
                    </label>
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={() => navigate("/generate")}
            style={{ marginTop: 16, padding: "10px 30px", background: "#4caf50", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 16 }}
          >
            开始生成 →
          </button>
        </>
      )}
    </div>
  );
}
