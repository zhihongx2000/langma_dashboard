import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Landing from './pages/Landing';
import EducationTools from './pages/EducationTools';
import PersonaAnalysis from './pages/PersonaAnalysis';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/education-tools" element={<EducationTools />} />
        <Route path="/persona-analysis" element={<PersonaAnalysis />} />
      </Routes>
    </BrowserRouter>
  );
}

