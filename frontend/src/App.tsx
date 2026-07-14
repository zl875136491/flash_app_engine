import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { HomePlaceholder } from "@/pages/HomePlaceholder";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePlaceholder />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
