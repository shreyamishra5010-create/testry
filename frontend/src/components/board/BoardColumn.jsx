import { Plus, MoreHorizontal, GripVertical } from "lucide-react";
import { TaskCard } from "./TaskCard";

const half = (e, axis) => {
  const r = e.currentTarget.getBoundingClientRect();
  return axis === "x" ? e.clientX > r.left + r.width / 2 : e.clientY > r.top + r.height / 2;
};

export const BoardColumn = ({ col, visible, drag, colDrag, onDropAt, onColumnDrop, setDrag, setColDrag, setModal, deleteTask }) => {
  const shown = col.tasks.filter(visible);
  const siblings = () => col.tasks.filter((t) => t.id !== drag?.id);
  const dropOn = (target, after) => {
    if (!drag) return false;
    if (target.id !== drag.id) onDropAt(col.id, siblings().findIndex((t) => t.id === target.id) + (after ? 1 : 0));
    return true;
  };
  const onDrop = (e) => {
    e.preventDefault();
    if (colDrag) onColumnDrop(col, half(e, "x"));
    else onDropAt(col.id, siblings().length);
  };
  const cls = `column${drag ? " drop-ready" : ""}${colDrag?.id === col.id ? " column-dragging" : ""}`;
  return (
    <section className={cls} data-testid={`column-${col.id}`} onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <div className="column-head" draggable data-testid={`column-drag-${col.id}`}
        onDragStart={(e) => { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", `column-${col.id}`); setColDrag(col); }}
        onDragEnd={() => setColDrag(null)}>
        <div><GripVertical size={14} className="column-grip" /><span className="column-dot" style={{ background: col.color }} /><h2 data-testid={`column-name-${col.id}`}>{col.name}</h2><small data-testid={`column-count-${col.id}`}>{shown.length}</small></div>
        <button data-testid={`column-menu-${col.id}`} aria-label="Column settings" className="icon-button" onClick={() => setModal({ type: "column", column: col })}><MoreHorizontal size={18} /></button>
      </div>
      <div className="task-list">
        {shown.map((t) => (
          <TaskCard key={t.id} task={t} dragging={drag?.id === t.id}
            onDragStart={(e) => { e.stopPropagation(); e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(t.id)); setDrag(t); }}
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
