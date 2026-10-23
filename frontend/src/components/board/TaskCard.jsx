import { CalendarDays, MessageSquare, Trash2 } from "lucide-react";
import { initials } from "@/lib/api";

const shortDate = (d) => new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export const TaskCard = ({ task, dragging, draggable, onTouchStart, onEdit, onDelete, onComment, onDragStart, onDragEnd, onDropHere }) => {
  const overdue = task.due_date && new Date(`${task.due_date}T23:59:59`) < new Date();
  return (
    <article
      className={`task-card priority-${task.priority}${dragging ? " dragging" : ""}`}
      draggable={draggable}
      data-task-id={task.id}
      onTouchStart={onTouchStart}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => { e.preventDefault(); const r = e.currentTarget.getBoundingClientRect(); if (onDropHere(e.clientY > r.top + r.height / 2)) e.stopPropagation(); }}
      data-testid={`task-card-${task.id}`}
    >
      <button className="task-title" data-testid={`task-open-${task.id}`} onClick={onEdit}>{task.title}</button>
      {task.description && <p>{task.description}</p>}
      <div className="task-meta">
        <span className={`priority ${task.priority}`}>{task.priority}</span>
        {task.due_date && <span className={overdue ? "overdue" : "due"} data-testid={`task-due-${task.id}`}><CalendarDays size={13} />{shortDate(task.due_date)}</span>}
        <span className="task-spacer" />
        <button onClick={onComment} data-testid={`task-comments-${task.id}`} aria-label="Comments"><MessageSquare size={14} />{task.comment_count > 0 && <small>{task.comment_count}</small>}</button>
        <button onClick={onDelete} data-testid={`task-delete-${task.id}`} aria-label="Delete task"><Trash2 size={14} /></button>
        {task.assignee_name && <span className="avatar" title={task.assignee_name} data-testid={`task-assignee-${task.id}`}>{initials(task.assignee_name)}</span>}
      </div>
    </article>
  );
};
