import { useState, useEffect } from 'react';
import './World.css';

export function World() {
  const [prayer, setPrayer] = useState('');
  const [revelation, setRevelation] = useState('');
  const [newRevelation, setNewRevelation] = useState('');
  const [offerings, setOfferings] = useState<{ name: string; size: number; modified: number }[]>([]);
  const [selectedFile, setSelectedFile] = useState<{ name: string; content: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [prayerRes, revelationRes, altarRes] = await Promise.all([
        fetch('http://localhost:8000/agent/world/prayer'),
        fetch('http://localhost:8000/agent/world/revelation'),
        fetch('http://localhost:8000/agent/world/altar'),
      ]);

      if (prayerRes.ok) {
        const data = await prayerRes.json();
        setPrayer(data.content || '');
      }
      if (revelationRes.ok) {
        const data = await revelationRes.json();
        setRevelation(data.content || '');
      }
      if (altarRes.ok) {
        const data = await altarRes.json();
        setOfferings(data.offerings || []);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewFile = async (name: string) => {
    try {
      const res = await fetch(`http://localhost:8000/agent/world/altar/${encodeURIComponent(name)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedFile(data);
      }
    } catch (e) {
      console.error(e);
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
        <p className="page-subtitle">浏览祈祷书、发布神谕、领取祭品</p>
      </div>

      <div className="world-cards world-cards-3">
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

        <div className="world-card">
          <div className="card-header">
            <h3>⬡ 祭坛</h3>
            <button className="refresh-btn" onClick={fetchAll}>⟳</button>
          </div>
          <p className="card-desc">Agent 提交给造物主的成果</p>
          <div className="card-content">
            {offerings.length === 0 ? (
              <div className="empty-altar">祭坛为空，Agent 尚未提交任何成果</div>
            ) : (
              <div className="offerings-list">
                {offerings.map(o => (
                  <div key={o.name} className="offering-item" onClick={() => handleViewFile(o.name)}>
                    <span className="offering-icon">📄</span>
                    <span className="offering-name">{o.name}</span>
                    <span className="offering-size">{(o.size / 1024).toFixed(1)} KB</span>
                  </div>
                ))}
              </div>
            )}
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

      {selectedFile && (
        <div className="file-modal" onClick={() => setSelectedFile(null)}>
          <div className="file-modal-content" onClick={e => e.stopPropagation()}>
            <div className="file-modal-header">
              <h3>{selectedFile.name}</h3>
              <button className="icon-btn" onClick={() => setSelectedFile(null)}>✕</button>
            </div>
            <pre className="file-modal-body">{selectedFile.content}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
