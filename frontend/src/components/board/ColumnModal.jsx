import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Modal } from "@/components/Modal";

export const ColumnModal = ({ column, close, reload }) => {
  const [name, setName] = useState(column.name);
  const save = async (e) => {
    e.preventDefault();
    try { await api(`/columns/${column.id}`, { method: "PATCH", body: JSON.stringify({ name }) }); close(); reload(); }
    catch (err) { toast.error(err.message); }
  };
  const remove = async () => {
    const count = column.tasks.length;
    if (!window.confirm(`Delete "${column.name}"${count ? ` and its ${count} task${count > 1 ? "s" : ""}` : ""}? This cannot be undone.`)) return;
    try { await api(`/columns/${column.id}`, { method: "DELETE" }); close(); reload(); }
    catch (err) { toast.error(err.message); }
  };
  return (
    <Modal title="Column settings" close={close}>
      <form className="modal-form" onSubmit={save}>
        <label>Column name<input data-testid="column-name-input" value={name} onChange={(e) => setName(e.target.value)} required /></label>
        <button className="primary wide" data-testid="column-save-button">Save column</button>
      </form>
      <hr />
      <p className="muted small" data-testid="column-delete-note">Deleting this column also deletes the {column.tasks.length} task(s) inside it.</p>
      <button className="danger wide" data-testid="column-delete-button" onClick={remove}>Delete column</button>
    </Modal>
  );
};
