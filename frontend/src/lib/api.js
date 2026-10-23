const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = async (path, opts = {}) => {
  const token = localStorage.getItem("token");
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
};

export const initials = (name = "?") => name.split(" ").map((x) => x[0]).join("").slice(0, 2).toUpperCase();

// Mirrors the server's ordering: remove the task, then insert it at `index` in the target column.
export const reorder = (columns, task, columnId, index) =>
  columns
    .map((c) => ({ ...c, tasks: c.tasks.filter((t) => t.id !== task.id) }))
    .map((c) => (c.id !== columnId ? c : { ...c, tasks: [...c.tasks.slice(0, index), { ...task, column_id: columnId }, ...c.tasks.slice(index)] }));
