import { useApp } from "../store";

export default function Settings() {
  const { llmConfig, setLLMConfig, engineConfigs, setEngineConfigs } = useApp();

  const updateLLM = (key: keyof typeof llmConfig, value: string | number) => {
    setLLMConfig({ ...llmConfig, [key]: value });
  };

  const updateEngine = (engine: string, key: string, value: string) => {
    setEngineConfigs({
      ...engineConfigs,
      [engine]: { ...(engineConfigs[engine] || {}), [key]: value },
    });
  };

  const inputStyle: React.CSSProperties = {
    padding: "6px 10px",
    borderRadius: 4,
    border: "1px solid #ccc",
    width: "100%",
    boxSizing: "border-box",
  };

  const sectionStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    marginBottom: 4,
    fontWeight: 500,
    color: "#333",
  };

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>设置</h1>

      {/* LLM Config */}
      <div style={sectionStyle}>
        <h2 style={{ marginTop: 0 }}>LLM 大模型配置</h2>
        <p style={{ color: "#666", fontSize: 14 }}>角色识别使用的 LLM API</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          <div>
            <label style={labelStyle}>协议</label>
            <select value={llmConfig.provider} onChange={(e) => updateLLM("provider", e.target.value)} style={inputStyle}>
              <option value="openai_compat">OpenAI 兼容（DeepSeek/Qwen/GLM/Ollama）</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>模型</label>
            <input value={llmConfig.model} onChange={(e) => updateLLM("model", e.target.value)} style={inputStyle}
              placeholder="deepseek-chat / qwen-plus / glm-4-flash / claude-sonnet-4-5-20250514" />
          </div>
          <div>
            <label style={labelStyle}>API Base URL</label>
            <input value={llmConfig.base_url} onChange={(e) => updateLLM("base_url", e.target.value)} style={inputStyle}
              placeholder="https://api.deepseek.com/v1" />
          </div>
          <div>
            <label style={labelStyle}>API Key</label>
            <input type="password" value={llmConfig.api_key} onChange={(e) => updateLLM("api_key", e.target.value)} style={inputStyle}
              placeholder="sk-..." />
          </div>
        </div>

        <div style={{ marginTop: 12, fontSize: 13, color: "#999" }}>
          推荐：DeepSeek-V4-Flash（便宜） / Qwen-Long（长文） / GLM-4-Flash（免费调试）
        </div>
      </div>

      {/* TTS Engine Configs */}
      <div style={sectionStyle}>
        <h2 style={{ marginTop: 0 }}>TTS 引擎配置</h2>
        <p style={{ color: "#666", fontSize: 14 }}>
          云端引擎需要 API Key；本地引擎需要运行中的服务地址。Edge TTS 无需配置。
        </p>

        {/* Cloud: DashScope */}
        <h3 style={{ fontSize: 16 }}>阿里云 CosyVoice (DashScope)</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8, marginBottom: 16 }}>
          <input
            type="password"
            placeholder="DashScope API Key"
            value={(engineConfigs.dashscope || {}).api_key || ""}
            onChange={(e) => updateEngine("dashscope", "api_key", e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Cloud: Volcengine */}
        <h3 style={{ fontSize: 16 }}>火山引擎豆包 TTS</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
          <input
            placeholder="App ID"
            value={(engineConfigs.volcengine || {}).app_id || ""}
            onChange={(e) => updateEngine("volcengine", "app_id", e.target.value)}
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="Access Token"
            value={(engineConfigs.volcengine || {}).access_token || ""}
            onChange={(e) => updateEngine("volcengine", "access_token", e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Cloud: MiMo */}
        <h3 style={{ fontSize: 16 }}>小米 MiMo</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
          <input
            placeholder="Base URL"
            value={(engineConfigs.mimo || {}).base_url || ""}
            onChange={(e) => updateEngine("mimo", "base_url", e.target.value)}
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="API Key"
            value={(engineConfigs.mimo || {}).api_key || ""}
            onChange={(e) => updateEngine("mimo", "api_key", e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Local engines */}
        <h3 style={{ fontSize: 16 }}>本地引擎（需自行运行服务）</h3>
        {[
          { id: "cosyvoice_local", name: "CosyVoice 2", port: "50000" },
          { id: "gpt_sovits", name: "GPT-SoVITS", port: "9880" },
          { id: "indextts", name: "IndexTTS 2", port: "8000" },
          { id: "fish_speech", name: "Fish Speech", port: "8080" },
          { id: "f5_tts", name: "F5-TTS", port: "7860" },
          { id: "chattts", name: "ChatTTS", port: "9999" },
          { id: "sherpa_vits", name: "sherpa-onnx VITS", port: "" },
          { id: "sherpa_kokoro", name: "sherpa-onnx Kokoro", port: "" },
        ].map((eng) => (
          <div key={eng.id} style={{ marginBottom: 8 }}>
            <label style={labelStyle}>{eng.name}</label>
            <input
              placeholder={eng.port ? `http://127.0.0.1:${eng.port} 或 模型目录(sherpa)` : "模型目录路径"}
              value={(engineConfigs[eng.id] || {}).base_url || (engineConfigs[eng.id] || {}).model_dir || ""}
              onChange={(e) => {
                const val = e.target.value;
                if (val.startsWith("http")) {
                  updateEngine(eng.id, "base_url", val);
                } else {
                  updateEngine(eng.id, "model_dir", val);
                }
              }}
              style={inputStyle}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
