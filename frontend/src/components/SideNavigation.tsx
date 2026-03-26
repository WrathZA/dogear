import { NavLink } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

const NAV_LINKS = [
  { to: "/", label: "All Bookmarks" },
  { to: "/favourites", label: "Favourites" },
  { to: "/tags", label: "Tags" },
  { to: "/add", label: "Add New" },
  { to: "/task-config", label: "Task Config" },
];

export function SideNavigation() {
  return (
    <nav
      className="window"
      style={{ width: 180, minHeight: "100vh", borderRadius: 0, display: "flex", flexDirection: "column" }}
    >
      <div className="title-bar">
        <div className="title-bar-text">bookmark-it</div>
      </div>
      <div className="window-body" style={{ flex: 1, padding: "8px 4px" }}>
        <ul className="tree-view" style={{ margin: 0 }}>
          {NAV_LINKS.map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === "/"}
                style={({ isActive }) => ({ fontWeight: isActive ? "bold" : "normal", textDecoration: "none", color: "inherit" })}
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      <div style={{ padding: 8, borderTop: "1px solid #808080" }}>
        <ThemeToggle />
      </div>
    </nav>
  );
}
