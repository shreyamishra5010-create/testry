import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { api, initials } from "@/lib/api";
import { Header } from "@/components/Header";
import { Modal } from "@/components/Modal";

const BoardTile = ({ board, open }) => (
  <button className="board-tile" data-testid={`board-tile-${board.id}`} onClick={open}>
    <div className="board-tile-top"><span className="board-icon">▦</span><MoreHorizontal size={18} /></div>
    <h3>{board.name}</h3>
    <p>{board.description || "A shared space for focused work."}</p>
    <div className="tile-footer"><span>{board.task_count} tasks · {board.member_count} members</span><span className="avatar">{initials(board.owner_name)}</span></div>
  </button>
);

export default function DashboardPage({ user, onLogout }) {
  const [boards, setBoards] = useState([]);
  const [show, setShow] = useState(false);
  const [name, setName] = useState("");
  const nav = useNavigate();
  const load = useCallback(() => api("/boards").then(setBoards).catch((e) => toast.error(e.message)), []);
  useEffect(() => { load(); }, [load]);
  const create = async (e) => {
    e.preventDefault();
    try { const b = await api("/boards", { method: "POST", body: JSON.stringify({ name }) }); nav(`/board/${b.id}`); }
    catch (err) { toast.error(err.message); }
  };
  const sum = (k) => boards.reduce((a, b) => a + b[k], 0);
  return (
    <div className="app-shell">
      <Header user={user} onLogout={onLogout} />
      <main className="dashboard">
        <div className="page-heading">
          <div><p className="eyebrow">YOUR WORKSPACE</p><h1>Good morning, {user.name.split(" ")[0]} <span className="wave">✦</span></h1><p className="muted">Keep the important work moving forward.</p></div>
          <button className="primary" data-testid="create-board-button" onClick={() => setShow(true)}><Plus size={17} /> New board</button>
        </div>
        <div className="stats-row">
          <div><strong data-testid="stat-boards">{boards.length}</strong><span>Active boards</span></div>
          <div><strong data-testid="stat-tasks">{sum("task_count")}</strong><span>Open tasks</span></div>
          <div><strong data-testid="stat-due">{sum("due_soon")}</strong><span>Due this week</span></div>
        </div>
        <section>
          <div className="section-title"><h2>Your boards</h2><span>{boards.length} boards</span></div>
          <div className="board-grid">
            {boards.map((b) => <BoardTile key={b.id} board={b} open={() => nav(`/board/${b.id}`)} />)}
            <button className="new-tile" data-testid="empty-create-board-button" onClick={() => setShow(true)}><span><Plus size={21} /></span><b>Create a board</b><small>Start with a clean slate</small></button>
          </div>
        </section>
      </main>
      {show && (
        <Modal title="Create a new board" close={() => setShow(false)}>
          <form onSubmit={create} className="modal-form">
            <label>Board name<input autoFocus data-testid="new-board-name-input" required placeholder="e.g. Website refresh" onChange={(e) => setName(e.target.value)} /></label>
            <button className="primary wide" data-testid="new-board-submit-button">Create board <span>→</span></button>
          </form>
        </Modal>
      )}
    </div>
  );
}
