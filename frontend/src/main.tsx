import "98.css";
import "./index.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { SideNavigation } from "./components/SideNavigation";
import { AllBookmarks } from "./pages/AllBookmarks";
import { Favourites } from "./pages/Favourites";
import { Tags } from "./pages/Tags";
import { AddNew } from "./pages/AddNew";
import { TaskConfig } from "./pages/TaskConfig";

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <div className="app-shell">
        <SideNavigation />
        <main className="app-content">
          <Routes>
            <Route path="/" element={<AllBookmarks />} />
            <Route path="/favourites" element={<Favourites />} />
            <Route path="/tags" element={<Tags />} />
            <Route path="/add" element={<AddNew />} />
            <Route path="/task-config" element={<TaskConfig />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  </StrictMode>,
);
