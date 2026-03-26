import { useEffect, useState } from "react";

const STORAGE_KEY = "bookmark-it-theme";

export function ThemeToggle() {
  const [dark, setDark] = useState<boolean>(() => localStorage.getItem(STORAGE_KEY) === "dark");

  useEffect(() => {
    document.body.classList.toggle("dark", dark);
    localStorage.setItem(STORAGE_KEY, dark ? "dark" : "light");
  }, [dark]);

  return (
    <button onClick={() => setDark((d) => !d)} style={{ width: "100%" }}>
      {dark ? "Light mode" : "Dark mode"}
    </button>
  );
}
