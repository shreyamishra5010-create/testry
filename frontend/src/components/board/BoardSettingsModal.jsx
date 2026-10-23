import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Modal } from "@/components/Modal";

export const BoardSettingsModal = ({ board, close, setBoard }) => {
  const [form, setForm] = useState({ name: board.name, description: board.description || "" });
  const nav = useNavigate();
  const save = async (e) => {
    e.preventDefault();
    try { setBoard(await api(`/boards/${board.id}`, { method: "PATCH", body: JSON.stringify(form) })); close(); }
    catch (err) { toast.error(err.message); }
  };
  const remove = async () => {
    if (!window.confirm(`Delete "${board.name}" and everything in it?`)) return;
    try { await api(`/boards/${board.id}`, { method: "DELETE" }); nav("/"); }
    catch (err) { toast.error(err.message); }
  };
  return (
    <Modal title="Board settings" close={close}>
      <form className="modal-form" onSubmit={save}>
        <label>Board name<input required data-testid="board-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label>Description<textarea data-testid="board-description-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        <button className="primary wide" data-testid="board-save-button">Save board</button>
      </form>
      <hr />
      <button className="danger wide" data-testid="board-delete-button" onClick={remove}>Delete board</button>
    </Modal>
  );
};
