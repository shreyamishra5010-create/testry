import { useState } from "react";
import { Modal } from "@/components/Modal";

export const TaskModal = ({ task, column, board, close, save }) => {
  const [form, setForm] = useState(task || { column_id: column.id, priority: "medium" });
  const change = (key) => (e) => setForm({ ...form, [key]: e.target.value });
  return (
    <Modal title={task ? "Edit task" : "Add a task"} close={close}>
      <form className="modal-form" onSubmit={(e) => { e.preventDefault(); save(form); }}>
        <label>Title<input autoFocus required data-testid="task-title-input" value={form.title || ""} onChange={change("title")} /></label>
        <label>Description<textarea data-testid="task-description-input" value={form.description || ""} onChange={change("description")} /></label>
        <div className="form-grid">
          <label>Priority
            <select data-testid="task-priority-select" value={form.priority || "medium"} onChange={change("priority")}>
              <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
            </select>
          </label>
          <label>Due date<input data-testid="task-due-date-input" type="date" value={form.due_date || ""} onChange={change("due_date")} /></label>
        </div>
        <div className="form-grid">
          <label>Assignee
            <select data-testid="task-assignee-select" value={form.assignee_id || ""} onChange={change("assignee_id")}>
              <option value="">Unassigned</option>
              {board.members.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </label>
          <label>Column (move task)
            <select data-testid="task-column-select" value={form.column_id || column.id} onChange={change("column_id")}>
              {board.columns.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
        </div>
        <button className="primary wide" data-testid="task-save-button">{task ? "Save changes" : "Create task"}<span>→</span></button>
      </form>
    </Modal>
  );
};
