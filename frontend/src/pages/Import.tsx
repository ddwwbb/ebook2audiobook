import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp, type ChapterData } from "../store";

export default function Import() {
  const { setBook } = useApp();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<{ total: number; chapters: any[]; title: string } | null>(null);

  const handleFile = async (file: File) => {
    setLoading(true);
    setError("");
    setPreview(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/books/import", { method: "POST", body: formData });
      if (!res.ok) throw new Error(`导入失败: ${res.status}`);
      const data = await res.json();
      setPreview({ total: data.total_chapters, chapters: data.chapters, title: data.title });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (!preview) return;
    const chapters: ChapterData[] = preview.chapters.map((c) => ({
      index: c.index,
      title: c.title,
      text: c.text_preview, // Note: preview is truncated; full text needs separate fetch
    }));
    setBook(preview.title, "", chapters);
    navigate("/roles");
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>导入小说</h1>

      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileRef.current?.click()}
        style={{
          border: "2px dashed #aaa",
          borderRadius: 12,
          padding: 60,
          textAlign: "center",
          cursor: "pointer",
          background: "#fff",
          transition: "border-color 0.2s",
        }}
      >
        <p style={{ fontSize: 18, color: "#666", margin: 0 }}>
          {loading ? "解析中..." : "拖拽 TXT / EPUB 文件到此处，或点击选择"}
        </p>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.epub"
          style={{ display: "none" }}
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      {error && (
        <div style={{ marginTop: 16, padding: 12, background: "#fee", borderRadius: 8, color: "#c00" }}>
          {error}
        </div>
      )}

      {preview && (
        <div style={{ marginTop: 20 }}>
          <div style={{ background: "#fff", borderRadius: 8, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>{preview.title}</h2>
            <p>共 {preview.total} 章</p>
            <div style={{ maxHeight: 400, overflowY: "auto" }}>
              {preview.chapters.map((ch) => (
                <div key={ch.index} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #eee" }}>
                  <strong>{ch.title}</strong>
                  <span style={{ marginLeft: 8, color: "#999", fontSize: 13 }}>{ch.char_count} 字</span>
                  <p style={{ color: "#666", fontSize: 14, margin: "4px 0 0" }}>{ch.text_preview}</p>
                </div>
              ))}
            </div>
            <button
              onClick={handleConfirm}
              style={{ marginTop: 16, padding: "10px 30px", background: "#4fc3f7", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 16 }}
            >
              确认导入，进入角色识别 →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
