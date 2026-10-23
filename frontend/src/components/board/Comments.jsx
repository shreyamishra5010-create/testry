import { useCallback, useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, initials } from "@/lib/api";
import { Modal } from "@/components/Modal";

export const Comments = ({ task, close, user, onChange }) => {
  const [items, setItems] = useState([]);
  const [body, setBody] = useState("");
  const load = useCallback(() => api(`/tasks/${task.id}/comments`).then(setItems).catch((e) => toast.error(e.message)), [task.id]);
  useEffect(() => { load(); }, [load]);
  const act = async (fn) => { try { await fn(); await load(); onChange(); } catch (e) { toast.error(e.message); } };
  const submit = (e) => { e.preventDefault(); act(async () => { await api(`/tasks/${task.id}/comments`, { method: "POST", body: JSON.stringify({ body }) }); setBody(""); }); };
  return (
    <Modal title={`Comments · ${task.title}`} close={close}>
      <div className="comments" data-testid="comments-list">
        {items.map((c) => (
          <div className="comment" key={c.id} data-testid={`comment-${c.id}`}>
            <span className="avatar">{initials(c.author_name)}</span>
            <div><b>{c.author_name}</b><small>{new Date(c.created_at).toLocaleString()}</small><p>{c.body}</p></div>
            {c.user_id === user.id && <button data-testid={`comment-delete-${c.id}`} aria-label="Delete comment" onClick={() => act(() => api(`/comments/${c.id}`, { method: "DELETE" }))}><Trash2 size={14} /></button>}
          </div>
        ))}
        {!items.length && <p className="muted" data-testid="comments-empty">No comments yet. Start the conversation.</p>}
        <form className="comment-form" onSubmit={submit}>
          <input data-testid="comment-input" placeholder="Write a comment…" value={body} onChange={(e) => setBody(e.target.value)} required />
          <button className="primary" data-testid="comment-submit">Send</button>
        </form>
      </div>
    </Modal>
  );
};
