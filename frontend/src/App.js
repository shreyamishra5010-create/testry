import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { Toaster } from "sonner";
import { api } from "@/lib/api";
import AuthPage from "@/pages/AuthPage";
import DashboardPage from "@/pages/DashboardPage";
import BoardPage from "@/pages/BoardPage";

function AppContent() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(localStorage.getItem("token")));
  const nav = useNavigate();
  useEffect(() => {
    if (!localStorage.getItem("token")) return;
    api("/me").then((x) => setUser(x.user)).catch(() => localStorage.removeItem("token")).finally(() => setChecking(false));
  }, []);
  const logout = () => { localStorage.removeItem("token"); setUser(null); nav("/"); };
  if (checking) return <div className="loading">Loading…</div>;
  if (!user) return <AuthPage onAuth={setUser} />;
  return (
    <Routes>
      <Route path="/" element={<DashboardPage user={user} onLogout={logout} />} />
      <Route path="/board/:id" element={<BoardPage user={user} onLogout={logout} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
      <Toaster position="bottom-right" richColors />
    </BrowserRouter>
  );
}

export default App;
