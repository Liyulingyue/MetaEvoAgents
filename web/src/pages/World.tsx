import { useState, useEffect } from 'react';
import './World.css';

export function World() {
  const [prayer, setPrayer] = useState('');
  const [revelation, setRevelation] = useState('');
  const [newRevelation, setNewRevelation] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [prayerRes, revelationRes] = await Promise.all([
        fetch('http://localhost:8000/agent/world/prayer'),
        fetch('http://localhost:8000/agent/world/revelation'),
      ]);

      if (prayerRes.ok) {
        const data = await prayerRes.json();
        setPrayer(data.content || '');
      }
      if (revelationRes.ok) {
        const data = await revelationRes.json();
        setRevelation(data.content || '');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleWriteRevelation = async () => {
    if (!newRevelation.trim()) return;
    try {
      await fetch('http://localhost:8000/agent/world/revelation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: newRevelation }),
      });
      setNewRevelation('');
      await fetchAll();
    } catch (error) {
      console.error('Failed to write revelation:', error);
    }
  };

  if (loading) {
    return (
      <div className="world-page">
        <div className="world-header">
          <h1>◎ 世界</h1>
          <p className="page-subtitle">查看数字文明的演化历程</p>
        </div>
        <div className="loading">
          <div className="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="world-page">
      <div className="world-header">
        <h1>◎ 世界</h1>
        <p className="page-subtitle">浏览祈祷书、发布神谕</p>
      </div>

      <div className="world-cards">
        <div className="world-card">
          <div className="card-header">
            <h3>📜 祈祷书</h3>
            <button className="refresh-btn" onClick={fetchAll}>⟳</button>
          </div>
          <p className="card-desc">Agent 对造物主的祈求与低语</p>
          <div className="card-content">
            <pre className="book-content">{prayer || '(祈祷书为空)'}</pre>
          </div>
        </div>

        <div className="world-card revelation-card">
          <div className="card-header">
            <h3>💡 启示录</h3>
            <button className="refresh-btn" onClick={fetchAll}>⟳</button>
          </div>
          <p className="card-desc">来自造物主的神谕与真理</p>

          <div className="revelation-form">
            <textarea
              value={newRevelation}
              onChange={(e) => setNewRevelation(e.target.value)}
              placeholder="降下神谕..."
              className="revelation-input"
            />
            <button
              className="send-btn"
              onClick={handleWriteRevelation}
              disabled={!newRevelation.trim()}
            >
              💡 降下神谕
            </button>
          </div>

          <div className="card-content">
            <pre className="book-content">{revelation || '(启示录为空)'}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
