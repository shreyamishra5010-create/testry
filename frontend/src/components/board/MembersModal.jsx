import { useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { api, initials } from "@/lib/api";
import { Modal } from "@/components/Modal";

export const MembersModal = ({ board, user, close, setBoard }) => {
  const [email, setEmail] = useState("");
  const isOwner = board.owner_id === user.id;
  const call = async (path, opts, msg) => {
    try { setBoard(await api(path, opts)); toast.success(msg); setEmail(""); } catch (e) { toast.error(e.message); }
  };
  return (
    <Modal title="Board members" close={close}>
      <div className="comments" data-testid="members-list">
        {board.members.map((m) => (
          <div className="comment" key={m.id} data-testid={`member-row-${m.id}`}>
            <span className="avatar">{initials(m.name)}</span>
            <div><b>{m.name}</b><small>{m.role}</small><p>{m.email}</p></div>
            {isOwner && m.role !== "owner" && (
              <button data-testid={`member-remove-${m.id}`} aria-label={`Remove ${m.name}`} onClick={() => call(`/boards/${board.id}/members/${m.id}`, { method: "DELETE" }, `${m.name} removed`)}><X size={14} /></button>
            )}
          </div>
        ))}
        {isOwner ? (
          <form className="comment-form" onSubmit={(e) => { e.preventDefault(); call(`/boards/${board.id}/members`, { method: "POST", body: JSON.stringify({ email }) }, "Teammate added"); }}>
            <input data-testid="member-email-input" type="email" required placeholder="teammate@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            <button className="primary" data-testid="member-invite-submit">Invite</button>
          </form>
        ) : <p className="muted small" data-testid="members-owner-note">Only the board owner can invite or remove members.</p>}
      </div>
    </Modal>
  );
};
