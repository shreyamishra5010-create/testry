import { Search, Filter, User } from "lucide-react";

export const BoardToolbar = ({ filters, setFilters, members }) => {
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });
  return (
    <div className="toolbar">
      <div className="search"><Search size={17} /><input data-testid="task-search-input" placeholder="Search tasks…" value={filters.query} onChange={set("query")} /></div>
      <div className="filter"><Filter size={15} />
        <select data-testid="priority-filter" aria-label="Filter by priority" value={filters.priority} onChange={set("priority")}>
          <option value="all">All priorities</option><option value="high">High priority</option><option value="medium">Medium priority</option><option value="low">Low priority</option>
        </select>
      </div>
      <div className="filter"><User size={15} />
        <select data-testid="assignee-filter" aria-label="Filter by assignee" value={filters.assignee} onChange={set("assignee")}>
          <option value="all">Everyone</option><option value="none">Unassigned</option>
          {members.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </div>
      <button className="ghost" data-testid="filter-reset-button" onClick={() => setFilters({ query: "", priority: "all", assignee: "all" })}>Reset</button>
    </div>
  );
};

export const matches = (f) => (t) =>
  (!f.query || `${t.title} ${t.description}`.toLowerCase().includes(f.query.toLowerCase())) &&
  (f.priority === "all" || t.priority === f.priority) &&
  (f.assignee === "all" || (f.assignee === "none" ? !t.assignee_id : String(t.assignee_id) === f.assignee));
