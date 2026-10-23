import { Plus, MoreHorizontal } from "lucide-react";
import { TaskCard } from "./TaskCard";

export const BoardColumn = ({ col, visible, drag, onDropAt, setDrag, setModal, deleteTask }) => {
  const shown = col.tasks.filter(visible);
  const siblings = () => col.tasks.filter((t) => t.id !== drag?.id);
  const dropOn = (target, after) => {
    if (!drag || target.id === drag.id) return;
    onDropAt(col.id, siblings().findIndex((t) => t.id === target.id) + (after ? 1 : 0));
  };
  return (
    <section className={`column${drag ? " drop-ready" : ""}`} data-testid={`column-${col.id}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); onDropAt(col.id, siblings().length); }}>
      <div className="column-head">
        <div><span className="column-dot" style={{ background: col.color }} /><h2 data-testid={`column-name-${col.id}`}>{col.name}</h2><small data-testid={`column-count-${col.id}`}>{shown.length}</small></div>
        <button data-testid={`column-menu-${col.id}`} aria-label="Column settings" className="icon-button" onClick={() => setModal({ type: "column", column: col })}><MoreHorizontal size={18} /></button>
      </div>
      <div className="task-list">
        {shown.map((t) => (
          <TaskCard key={t.id} task={t} dragging={drag?.id === t.id}
            onDragStart={(e) => { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(t.id)); setDrag(t); }}
            onDragEnd={() => setDrag(null)}
            onDropHere={(after) => dropOn(t, after)}
            onEdit={() => setModal({ type: "task", task: t })}
            onDelete={() => deleteTask(t)}
            onComment={() => setModal({ type: "comments", task: t })} />
        ))}
      </div>
      <button className="add-task" data-testid={`add-task-${col.id}`} onClick={() => setModal({ type: "task", column: col })}><Plus size={16} /> Add task</button>
    </section>
  );
};
