import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "@/pages/Index";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        {/* Add more routes here if needed */}
        <Route path="*" element={<div className="text-center text-white text-xl p-10">404: Page Not Found</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
