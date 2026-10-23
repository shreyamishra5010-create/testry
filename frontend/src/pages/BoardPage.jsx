import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Plus, Settings } from "lucide-react";
import { toast } from "sonner";
import { api, initials, reorder } from "@/lib/api";
import { Header } from "@/components/Header";
import { SimpleModal } from "@/components/Modal";
import { BoardToolbar, matches } from "@/components/board/BoardToolbar";
import { BoardColumn } from "@/components/board/BoardColumn";
import { TaskModal } from "@/components/board/TaskModal";
import { ColumnModal } from "@/components/board/ColumnModal";
import { Comments } from "@/components/board/Comments";
import { MembersModal } from "@/components/board/MembersModal";
import { BoardSettingsModal } from "@/components/board/BoardSettingsModal";

export default function BoardPage({ user, onLogout }) {
  const { id } = useParams();
  const nav = useNavigate();
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ query: "", priority: "all", assignee: "all" });
  const [modal, setModal] = useState(null);
  const [drag, setDrag] = useState(null);
  const load = useCallback(() => api(`/boards/${id}`).then(setBoard).catch((e) => setError(e.message)), [id]);
  useEffect(() => { load(); }, [load]);

  const attempt = async (fn) => { try { await fn(); } catch (e) { toast.error(e.message); } finally { load(); } };
  const close = () => setModal(null);

  if (error) return (
    <div className="app-shell"><Header user={user} onLogout={onLogout} />
      <main className="dashboard" data-testid="board-error"><p className="eyebrow">CAN'T OPEN BOARD</p><h1 className="error-title">{error}</h1><p className="muted">Ask the board owner to invite you, or head back to your boards.</p><button className="primary" data-testid="board-error-back" onClick={() => nav("/")}>← Back to boards</button></main>
    </div>
  );
  if (!board) return <div className="loading">Loading board…</div>;

  const onDropAt = (columnId, index) => {
    if (!drag) return;
    const task = drag;
    setDrag(null);
    setBoard((b) => ({ ...b, columns: reorder(b.columns, task, columnId, index) }));
    attempt(() => api(`/tasks/${task.id}/move`, { method: "PATCH", body: JSON.stringify({ column_id: columnId, position: index }) }));
  };
  const saveTask = (d) => attempt(async () => {
    if (modal.task) await api(`/tasks/${modal.task.id}`, { method: "PATCH", body: JSON.stringify(d) });
    else await api(`/boards/${id}/tasks`, { method: "POST", body: JSON.stringify(d) });
    close();
  });
  const deleteTask = (t) => window.confirm(`Delete "${t.title}"?`) && attempt(() => api(`/tasks/${t.id}`, { method: "DELETE" }));
  const addColumn = (name) => attempt(async () => { await api(`/boards/${id}/columns`, { method: "POST", body: JSON.stringify({ name }) }); close(); });

  return (
    <div className="app-shell board-page">
      <Header user={user} onLogout={onLogout} />
      <main className="board-main">
        <div className="board-heading">
          <div>
            <button className="back-button" data-testid="back-to-dashboard" onClick={() => nav("/")}>← All boards</button>
            <h1 data-testid="board-title">{board.name}</h1><p>{board.description}</p>
          </div>
          <div className="member-stack">
            {board.members.map((m) => <span key={m.id} title={m.name} data-testid={`member-avatar-${m.id}`}>{initials(m.name)}</span>)}
            <button className="add-member" data-testid="add-member-button" aria-label="Manage members" onClick={() => setModal({ type: "member" })}><Plus size={15} /></button>
            {board.owner_id === user.id && <button className="icon-button board-settings" data-testid="board-settings-button" aria-label="Board settings" onClick={() => setModal({ type: "board" })}><Settings size={17} /></button>}
          </div>
        </div>
        <BoardToolbar filters={filters} setFilters={setFilters} members={board.members} />
        <div className="columns" data-testid="kanban-board">
          {board.columns.map((col) => <BoardColumn key={col.id} col={col} visible={matches(filters)} drag={drag} setDrag={setDrag} onDropAt={onDropAt} setModal={setModal} deleteTask={deleteTask} />)}
          <button className="add-column" data-testid="add-column-button" onClick={() => setModal({ type: "add-column" })}><Plus size={18} /> Add column</button>
        </div>
      </main>
      {modal?.type === "task" && <TaskModal task={modal.task} column={modal.column || board.columns[0]} board={board} close={close} save={saveTask} />}
      {modal?.type === "comments" && <Comments task={modal.task} close={close} user={user} onChange={load} />}
      {modal?.type === "add-column" && <SimpleModal title="Add column" placeholder="Column name" close={close} onSave={addColumn} />}
      {modal?.type === "column" && <ColumnModal column={modal.column} close={close} reload={load} />}
      {modal?.type === "member" && <MembersModal board={board} user={user} close={close} setBoard={setBoard} />}
      {modal?.type === "board" && <BoardSettingsModal board={board} close={close} setBoard={setBoard} />}
    </div>
  );
}
