import { useState } from "react";
import { api } from "@/lib/api";

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({});
  const [error, setError] = useState("");
  const isLogin = mode === "login";
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const d = await api(`/auth/${mode}`, { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("token", d.token);
      onAuth(d.user);
    } catch (err) { setError(err.message); }
  };
  return (
    <main className="auth-shell">
      <section className="auth-art">
        <div className="brand-mark">▦</div><span className="eyebrow">NORTHSTAR WORKSPACE</span>
        <h1>Make progress<br /><em>visible.</em></h1>
        <p>A calm, focused home for the work that moves your team forward.</p>
        <div className="mini-board"><span>Discovery</span><span>Build</span><span>Ship</span></div>
      </section>
      <section className="auth-panel">
        <div className="auth-form">
          <div className="mobile-logo">▦ Northstar</div>
          <p className="eyebrow">{isLogin ? "WELCOME BACK" : "CREATE YOUR WORKSPACE"}</p>
          <h2>{isLogin ? "Sign in to your board" : "Start organizing your work"}</h2>
          <p className="muted">{isLogin ? "Pick up where you left off." : "A simple, powerful space for your team."}</p>
          {error && <div className="alert" data-testid="auth-error">{error}</div>}
          <form onSubmit={submit}>
            {!isLogin && <label>Name<input data-testid="register-name-input" required placeholder="Alex Morgan" onChange={set("name")} /></label>}
            <label>Email<input data-testid={`${mode}-email-input`} type="email" required placeholder="you@company.com" onChange={set("email")} /></label>
            <label>Password<input data-testid={`${mode}-password-input`} type="password" required minLength="8" placeholder="8+ characters" onChange={set("password")} /></label>
            <button className="primary wide" data-testid={`${mode}-submit-button`}>{isLogin ? "Sign in" : "Create account"}<span>→</span></button>
          </form>
          <button className="text-button" data-testid="auth-mode-toggle" onClick={() => { setMode(isLogin ? "register" : "login"); setError(""); }}>
            {isLogin ? "New here? Create an account" : "Already have an account? Sign in"}
          </button>
          <p className="tiny">Demo access: demo@taskboard.local · demo1234</p>
        </div>
      </section>
    </main>
  );
}
