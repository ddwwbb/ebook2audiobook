import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { AppProvider } from "./store";
import Import from "./pages/Import";
import Roles from "./pages/Roles";
import Voices from "./pages/Voices";
import Generate from "./pages/Generate";
import Settings from "./pages/Settings";

const navItems = [
  { to: "/", label: "1. 导入" },
  { to: "/roles", label: "2. 角色识别" },
  { to: "/voices", label: "3. 音色分配" },
  { to: "/generate", label: "4. 生成" },
  { to: "/settings", label: "设置" },
];

const navStyle: React.CSSProperties = {
  width: 200,
  background: "#1a1a2e",
  color: "#fff",
  padding: "20px 0",
  minHeight: "100vh",
  flexShrink: 0,
};

const linkStyle = (isActive: boolean): React.CSSProperties => ({
  display: "block",
  padding: "12px 20px",
  color: isActive ? "#4fc3f7" : "#ccc",
  textDecoration: "none",
  background: isActive ? "rgba(79,195,247,0.1)" : "transparent",
  borderLeft: isActive ? "3px solid #4fc3f7" : "3px solid transparent",
  transition: "all 0.2s",
});

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <div style={{ display: "flex", fontFamily: "system-ui, -apple-system, sans-serif" }}>
          <nav style={navStyle}>
            <h2 style={{ padding: "0 20px 20px", fontSize: 18, borderBottom: "1px solid #333" }}>
              📚 Audiobook Studio
            </h2>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {navItems.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} style={({ isActive }) => linkStyle(isActive)} end={item.to === "/"}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <main style={{ flex: 1, padding: 30, background: "#f5f5f5", minHeight: "100vh" }}>
            <Routes>
              <Route path="/" element={<Import />} />
              <Route path="/roles" element={<Roles />} />
              <Route path="/voices" element={<Voices />} />
              <Route path="/generate" element={<Generate />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AppProvider>
  );
}
