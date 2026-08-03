# Audiobook Studio

中文小说分角色有声书 AI 工具:把 EPUB/TXT 小说自动拆分为角色对白,用 LLM 标注角色,再用可切换的 TTS 引擎合成多角色有声书。

- **后端**:Python FastAPI(REST + WebSocket),入口 `backend/main.py`
- **前端**:React 19 + TypeScript + Vite 6 SPA
- **桌面壳**:Tauri 2(Mac/Win/Linux,x64 + arm64)
- **容器**:多阶段 Docker 镜像(内置 ffmpeg / calibre / espeak-ng),无桌面环境用浏览器访问

## 项目结构

```
.
├── backend/                # FastAPI 后端
│   ├── main.py             # 入口:create_app()
│   ├── api/                # REST 路由
│   │   ├── routes_books.py     # /api/books    导入与解析
│   │   ├── routes_roles.py     # /api/roles    角色识别与分配
│   │   ├── routes_voices.py    # /api/voices   引擎元数据与音色
│   │   └── routes_generate.py  # /api/generate 合成任务
│   ├── e2a/parser.py       # EPUB/TXT 文本解析
│   ├── llm/                # LLM 客户端(openai_compat / anthropic)
│   ├── tts/                # 12 个 TTS 引擎 + 工厂
│   ├── audio/              # SML 解析、合成、静音、合并、导出
│   ├── pipeline/           # single_pass / two_pass 流水线
│   └── packer/epub_packer.py
├── frontend/               # React + Vite SPA
│   └── src/pages/          # Import / Roles / Voices / Generate / Settings
├── tauri/                  # Tauri 2 桌面壳
├── docker/                 # Dockerfile / Dockerfile.arm64 / compose
├── scripts/dev.sh          # 一键启动前后端
├── LICENSE
└── README.md
```

## 架构

```
EPUB/TXT ──▶ e2a/parser ──▶ pipeline(single_pass | two_pass)
                                    │
                                    ├─ llm/factory ──▶ 角色标注 / 文本规范化
                                    │                  (openai_compat | anthropic)
                                    │
                                    ├─ tts/factory ──▶ 12 个引擎任选
                                    │
                                    └─ audio/ ──▶ sml_parser → synthesizer
                                                 → silence → merger → exporter
                                                 → m4b / mp3 / ...
```

- **单遍 (single_pass)**:一次扫描直接合成;适合短篇或快速预览。
- **双遍 (two_pass)**:第一遍识别角色与场景,第二遍按角色切换音色合成;适合长篇小说。

## TTS 引擎(12)

| ID | 名称 | 类型 | 克隆 | 协议 |
|---|---|---|:---:|---|
| `edge` | Edge TTS | 云端 | ❌ | free |
| `dashscope` | 阿里 CosyVoice | 云端 | ✅ | DashScope |
| `volcengine` | 火山豆包 TTS | 云端 | ✅ | WebSocket V3 |
| `mimo` | 小米 MiMo | 云端 | ✅ | OpenAI 兼容 |
| `cosyvoice_local` | CosyVoice 2 | 本地 HTTP | ✅ | Apache-2.0 |
| `gpt_sovits` | GPT-SoVITS V4 | 本地 HTTP | ✅ | MIT |
| `indextts` | IndexTTS 2 | 本地 HTTP | ✅ | bilibili |
| `fish_speech` | Fish Speech | 本地 HTTP | ✅ | Fish License |
| `f5_tts` | F5-TTS | 本地 HTTP | ✅ | CC-BY-NC(权重)|
| `chattts` | ChatTTS | 本地 HTTP | ❌ | CC-BY-NC |
| `sherpa_vits` | sherpa-onnx VITS | 本地 ONNX | ❌ | Apache-2.0 |
| `sherpa_kokoro` | sherpa-onnx Kokoro | 本地 ONNX | ❌ | Apache-2.0 |

引擎元数据见 `backend/tts/factory.py` 中的 `ENGINE_METADATA`,前端 `/api/voices` 直接消费。

## LLM

后端通过 `llm/factory.py` 提供 2 种 provider:

- **`openai_compat`**:任何 OpenAI 兼容 API(DeepSeek、Qwen、GLM、Kimi 等)
- **`anthropic`**:Anthropic Claude

推荐模型(走 `openai_compat`):

| 模型 | 上下文 | 备注 |
|---|---|---|
| DeepSeek-V3 / V4 | 128K+ | 生产首选 |
| Qwen-Long | 1M | 超长文批处理 |
| GLM-4-Flash | 128K | 免费调试 |

## 开发

环境要求:Python ≥ 3.11、Node ≥ 20、ffmpeg。

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 7860
```

```bash
# 前端(另一个终端)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

一键启动(同时拉起前后端):

```bash
./scripts/dev.sh
```

开发模式下,前端 Vite 跑在 `5173`,通过 CORS 代理到后端 `7860`;生产构建后,FastAPI 会在 `/` 静态托管 `frontend/dist`。

## Docker

```bash
cd docker
docker compose up -d
# → http://localhost:7860
```

默认 `Dockerfile` 为 x86_64,多阶段构建:Stage 1 用 Node 编译前端,Stage 2 用 Python 运行时并安装 ffmpeg、calibre、espeak-ng。

RK3588 / ARM64:

```bash
docker build -f docker/Dockerfile.arm64 -t audiobook-studio:arm64 .
docker run -p 7860:7860 \
  -v ./books:/books:ro \
  -v ./output:/app/output \
  audiobook-studio:arm64
```

### RK3588 定位

RK3588 作为**轻量客户端**:本地只跑 FastAPI Web 服务、EPUB 解析与音频拼接,**LLM 与 TTS 应走云端 API**(Edge / DashScope / 火山 / 小米)。算力允许时也可跑 sherpa-onnx 本地小模型,但**不建议**在板端跑本地大参数 TTS 或 LLM。

## 桌面应用(Tauri)

```bash
cd tauri
npm install        # 前端依赖(在 frontend/ 已装可跳过)
cargo tauri dev    # 开发
cargo tauri build  # 打包(Mac/Win/Linux,x64 + arm64)
```

Tauri 启动时会自动执行 `frontend/` 的 `npm run dev` 或 `npm run build`(见 `tauri.conf.json` 的 `beforeDevCommand` / `beforeBuildCommand`)。

## 测试

```bash
cd backend
pip install pytest        # 未在 requirements.txt 中,需单独安装
pytest
```

覆盖 EPUB 打包、LLM 客户端、本地 TTS、流水线、SML 解析、TTS 工厂、TXT 解析等(见 `backend/tests/`)。

## API 概览

| 路由 | 说明 |
|---|---|
| `GET  /api/health` | 健康检查 |
| `*   /api/books` | 导入与解析图书 |
| `*   /api/roles` | 角色识别与音色分配 |
| `*   /api/voices` | TTS 引擎与音色元数据 |
| `*   /api/generate` | 合成任务(同步 / WebSocket 进度) |
