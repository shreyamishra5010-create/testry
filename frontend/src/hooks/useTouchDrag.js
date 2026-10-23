import { useCallback, useEffect, useRef } from "react";

const HOLD_MS = 350;
const SLOP = 8;
const EDGE = 48;
const SPEED = 14;

export const isTouchDevice = () => typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;

// Press-and-hold drag for touch screens. onBegin(item) / onEnd() toggle drag state; onDrop(item, x, y) resolves the target.
export function useTouchDrag({ onBegin, onEnd, onDrop, scrollEl }) {
  const cb = useRef({});
  cb.current = { onBegin, onEnd, onDrop, scrollEl };
  const s = useRef(null);

  const cleanup = useCallback(() => {
    const st = s.current;
    if (!st) return;
    clearTimeout(st.timer);
    cancelAnimationFrame(st.raf);
    st.ghost?.remove();
    window.removeEventListener("touchmove", st.move);
    window.removeEventListener("touchend", st.end);
    window.removeEventListener("touchcancel", st.cancel);
    s.current = null;
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const autoScroll = useCallback(() => {
    const st = s.current;
    if (!st?.active) return;
    const { x, y } = st;
    const dx = x < EDGE ? -SPEED : x > window.innerWidth - EDGE ? SPEED : 0;
    const dy = y < EDGE ? -SPEED : y > window.innerHeight - EDGE ? SPEED : 0;
    if (dx) cb.current.scrollEl?.current?.scrollBy(dx, 0);
    if (dy) window.scrollBy(0, dy);
    st.raf = requestAnimationFrame(autoScroll);
  }, []);

  const start = useCallback((e, item, sourceEl) => {
    if (e.touches.length !== 1 || s.current) return;
    const t = e.touches[0];
    const st = { item, x: t.clientX, y: t.clientY, ox: t.clientX, oy: t.clientY, active: false };
    st.move = (ev) => {
      const p = ev.touches[0];
      st.x = p.clientX; st.y = p.clientY;
      if (!st.active) {
        if (Math.hypot(st.x - st.ox, st.y - st.oy) > SLOP) cleanup();
        return;
      }
      ev.preventDefault();
      st.ghost.style.transform = `translate(${st.x - st.dx}px, ${st.y - st.dy}px) rotate(2deg)`;
    };
    st.end = (ev) => {
      if (st.active) {
        ev.preventDefault();
        cb.current.onDrop(st.item, st.x, st.y);
        cb.current.onEnd();
      }
      cleanup();
    };
    st.cancel = () => { if (st.active) cb.current.onEnd(); cleanup(); };
    st.timer = setTimeout(() => {
      const r = sourceEl.getBoundingClientRect();
      const ghost = sourceEl.cloneNode(true);
      ghost.className += " touch-ghost";
      ghost.removeAttribute("data-testid");
      ghost.querySelectorAll("[data-testid]").forEach((n) => n.removeAttribute("data-testid"));
      Object.assign(ghost.style, { width: `${r.width}px`, left: "0px", top: "0px" });
      st.dx = st.x - r.left; st.dy = st.y - r.top;
      ghost.style.transform = `translate(${r.left}px, ${r.top}px) rotate(2deg)`;
      document.body.appendChild(ghost);
      st.ghost = ghost;
      st.active = true;
      navigator.vibrate?.(15);
      cb.current.onBegin(st.item);
      st.raf = requestAnimationFrame(autoScroll);
    }, HOLD_MS);
    window.addEventListener("touchmove", st.move, { passive: false });
    window.addEventListener("touchend", st.end, { passive: false });
    window.addEventListener("touchcancel", st.cancel);
    s.current = st;
  }, [cleanup, autoScroll]);

  return start;
}
