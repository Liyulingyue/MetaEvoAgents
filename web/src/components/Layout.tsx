import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">⬡</span>
            <span className="logo-text">MetaEvoAgents</span>
          </div>
          <nav className="nav">
            <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
              <span className="nav-icon">◈</span>
              对话
            </Link>
            <Link to="/lineages" className={`nav-link ${isActive('/lineages') ? 'active' : ''}`}>
              <span className="nav-icon">◉</span>
              Lineages
            </Link>
            <Link to="/vault" className={`nav-link ${isActive('/vault') ? 'active' : ''}`}>
              <span className="nav-icon">📁</span>
              文件区
            </Link>
            <Link to="/observer" className={`nav-link ${isActive('/observer') ? 'active' : ''}`}>
              <span className="nav-icon">👁️</span>
              观察
            </Link>
            <Link to="/world" className={`nav-link ${isActive('/world') ? 'active' : ''}`}>
              <span className="nav-icon">◎</span>
              世界
            </Link>
            <Link to="/admin" className={`nav-link ${isActive('/admin') ? 'active' : ''}`}>
              <span className="nav-icon">⚙️</span>
              管理
            </Link>
          </nav>
          <div className="header-status">
            <span className="status-indicator"></span>
            <span className="status-text">系统运行中</span>
          </div>
        </div>
      </header>
      <main className="main">
        {children}
      </main>
      <footer className="footer">
        <p>MetaEvoAgents - 数字文明演化模拟器</p>
      </footer>
    </div>
  );
}
