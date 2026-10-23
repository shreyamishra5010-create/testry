import { useState } from "react";
import { X } from "lucide-react";

export const Modal = ({ title, close, children }) => (
  <div className="modal-backdrop" data-testid="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close()}>
    <div className="modal" role="dialog" aria-label={title}>
      <div className="modal-head">
        <h2>{title}</h2>
        <button className="icon-button" data-testid="modal-close-button" aria-label="Close" onClick={close}><X size={18} /></button>
      </div>
      {children}
    </div>
  </div>
);

export const SimpleModal = ({ title, close, onSave, placeholder, type = "text", initial = "" }) => {
  const [value, setValue] = useState(initial);
  return (
    <Modal title={title} close={close}>
      <form className="modal-form" onSubmit={(e) => { e.preventDefault(); onSave(value); }}>
        <label>{title}<input autoFocus required type={type} data-testid="simple-modal-input" placeholder={placeholder} value={value} onChange={(e) => setValue(e.target.value)} /></label>
        <button className="primary wide" data-testid="simple-modal-submit">Save <span>→</span></button>
      </form>
    </Modal>
  );
};
