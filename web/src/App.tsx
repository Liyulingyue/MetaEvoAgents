import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Lineages } from './pages/Lineages';
import { LineageDetailPage } from './pages/LineageDetailPage';
import { VaultBrowser } from './pages/VaultBrowser';
import { World } from './pages/World';
import { Observer } from './pages/Observer';
import { Admin } from './pages/Admin';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lineages" element={<Lineages />} />
          <Route path="/lineages/:id" element={<LineageDetailPage />} />
          <Route path="/vault" element={<VaultBrowser />} />
          <Route path="/world" element={<World />} />
          <Route path="/observer" element={<Observer />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
