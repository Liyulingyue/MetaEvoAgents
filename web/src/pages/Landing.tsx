import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';

const features = [
  {
    icon: '◈',
    title: '多 Agent 协作',
    desc: '多个宗族 Agent 并行运作，彼此通信协作，共同解决复杂任务',
  },
  {
    icon: '◎',
    title: '持久演化',
    desc: 'Agent 在每次任务中积累经验、沉淀记忆，形成独特的演化路径',
  },
  {
    icon: '⬡',
    title: '文件记忆',
    desc: '每个宗族拥有独立的文件存储空间，在演化中不断积累知识资产',
  },
  {
    icon: '◉',
    title: '守护进程',
    desc: 'Agent 以独立后台进程形式持续运行，即使关闭网页其思考与演化也不会中断',
  },
];

export function Landing() {
  const [lineageCount, setLineageCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/agent/lineages')
      .then(r => r.ok ? r.json() : [])
      .then(data => setLineageCount(Array.isArray(data) ? data.length : 0))
      .catch(() => setLineageCount(0))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="landing">
      <div className="landing-grid-bg"></div>
      <section className="hero">
        <div className="hero-badge">数字文明演化模拟器</div>
        <h1 className="hero-title">MetaEvoAgents</h1>
        <p className="hero-desc">
          多 Agent 智能体协同演化平台。<br />
          创造宗族、观察演化、与 AI Agent 纵论文明。
        </p>
        <div className="hero-cta">
          <Link to="/chat" className="cta-primary">
            开始对话 ◈
          </Link>
          <Link to="/lineages" className="cta-secondary">
            管理宗族 ◉
          </Link>
        </div>
        {!loading && lineageCount > 0 && (
          <div className="hero-stat">
            <span className="pulse-dot"></span>
            当前共有 <strong>{lineageCount}</strong> 个宗族正在后台常驻运行
          </div>
        )}
      </section>

      <section className="features">
        <h2 className="features-title">系统特性</h2>
        <div className="features-grid">
          {features.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="quick-nav">
        <h2 className="nav-title">快速导航</h2>
        <div className="nav-grid">
          <Link to="/chat" className="nav-card">
            <span className="nav-icon">◈</span>
            <span className="nav-label">对话</span>
            <span className="nav-hint">与 Agent 直接对话</span>
          </Link>
          <Link to="/lineages" className="nav-card">
            <span className="nav-icon">◉</span>
            <span className="nav-label">宗族</span>
            <span className="nav-hint">管理所有 Agent 实体</span>
          </Link>
          <Link to="/observer" className="nav-card">
            <span className="nav-icon">👁️</span>
            <span className="nav-label">观察</span>
            <span className="nav-hint">实时观察 Agent 活动</span>
          </Link>
          <Link to="/world" className="nav-card">
            <span className="nav-icon">◎</span>
            <span className="nav-label">世界</span>
            <span className="nav-hint">祈祷书与启示录</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
