import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { initials } from "@/lib/api";

export const Header = ({ user, onLogout }) => {
  const nav = useNavigate();
  return (
    <header className="topbar">
      <button className="logo" data-testid="app-logo" onClick={() => nav("/")}><span>▦</span> northstar</button>
      <div className="topbar-right">
        <span className="online"><i /> Workspace online</span>
        <span className="user-chip" data-testid="current-user"><b>{initials(user.name)}</b>{user.name}</span>
        <button className="logout" data-testid="logout-button" aria-label="Log out" onClick={onLogout}><LogOut size={16} /></button>
      </div>
    </header>
  );
};
