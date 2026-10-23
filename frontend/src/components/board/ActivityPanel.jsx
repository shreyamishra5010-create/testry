import { useCallback, useEffect, useState } from "react";
import { X, ListChecks, MessageSquare, Columns3, ArrowRightLeft, Trash2, Pencil } from "lucide-react";
import { api, initials } from "@/lib/api";

const ICONS = { task: ListChecks, comment: MessageSquare, column: Columns3 };
const iconFor = (action) => (action.endsWith("deleted") ? Trash2 : action.endsWith("moved") || action.endsWith("reordered") ? ArrowRightLeft : action.endsWith("updated") || action.endsWith("renamed") ? Pencil : ICONS[action.split(".")[0]] || ListChecks);

const ago = (iso) => {
  const s = Math.max(0, (Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 604800) return `${Math.floor(s / 86400)}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

export const ActivityPanel = ({ boardId, version, close }) => {
  const [items, setItems] = useState(null);
  const load = useCallback(() => api(`/boards/${boardId}/activity`).then(setItems).catch(() => setItems([])), [boardId]);
  useEffect(() => { load(); }, [load, version]);
  return (
    <>
      <div className="activity-scrim" onClick={close} />
      <aside className="activity-panel" data-testid="activity-panel" aria-label="Board activity">
        <div className="activity-head">
          <div><p className="eyebrow">TIMELINE</p><h2>Activity</h2></div>
          <button className="icon-button" data-testid="activity-close-button" aria-label="Close activity" onClick={close}><X size={18} /></button>
        </div>
        {items === null && <p className="muted small">Loading…</p>}
        {items?.length === 0 && <p className="muted small" data-testid="activity-empty">No activity yet. Changes on this board will show up here.</p>}
        <ol className="activity-list">
          {items?.map((a) => {
            const Icon = iconFor(a.action);
            return (
              <li key={a.id} data-testid={`activity-item-${a.id}`}>
                <span className="avatar">{initials(a.user_name)}</span>
                <div><p><b>{a.user_name}</b> {a.message}</p><small><Icon size={12} /> {ago(a.created_at)}</small></div>
              </li>
            );
          })}
        </ol>
      </aside>
    </>
  );
};
