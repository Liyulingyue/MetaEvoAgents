import { useState, useEffect } from 'react';
import type { Lineage } from '../types';
import './Admin.css';

interface Template {
  id: string;
  name: string;
  desc: string;
}

export function Admin() {
  const [lineages, setLineages] = useState<Lineage[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [newName, setNewName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [lineagesRes, templatesRes] = await Promise.all([
        fetch('http://localhost:8000/agent/lineages'),
        fetch('http://localhost:8000/agent/templates'),
      ]);

      if (lineagesRes.ok) {
        const data = await lineagesRes.json();
        setLineages(data);
      }
      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data.templates);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleCreate = async () => {
    if (!newName.trim()) {
      showMessage('error', '请输入 Lineage 名称');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/agent/lineages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, template: selectedTemplate }),
      });

      const data = await response.json();
      if (response.ok) {
        showMessage('success', data.message);
        setNewName('');
        fetchData();
      } else {
        showMessage('error', data.detail);
      }
    } catch (err) {
      showMessage('error', '创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (lineageId: string) => {
    if (confirmAction !== lineageId) {
      setConfirmAction(lineageId);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/agent/lineages/${lineageId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (response.ok) {
        showMessage('success', data.message);
        fetchData();
      } else {
        showMessage('error', data.detail);
      }
    } catch (err) {
      showMessage('error', '删除失败');
    } finally {
      setLoading(false);
      setConfirmAction(null);
    }
  };

  const handleReset = async () => {
    if (confirmAction !== 'reset') {
      setConfirmAction('reset');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/agent/reset', {
        method: 'POST',
      });

      const data = await response.json();
      if (response.ok) {
        showMessage('success', data.message);
        fetchData();
      } else {
        showMessage('error', data.detail);
      }
    } catch (err) {
      showMessage('error', '重置失败');
    } finally {
      setLoading(false);
      setConfirmAction(null);
    }
  };

  const handleClear = async () => {
    if (confirmAction !== 'clear') {
      setConfirmAction('clear');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/agent/clear', {
        method: 'POST',
      });

      const data = await response.json();
      if (response.ok) {
        showMessage('success', data.message);
        fetchData();
      } else {
        showMessage('error', data.detail);
      }
    } catch (err) {
      showMessage('error', '清空失败');
    } finally {
      setLoading(false);
      setConfirmAction(null);
    }
  };

  return (
    <div className="admin">
      <div className="admin-header">
        <h2>⚙️ 管理</h2>
        <p className="admin-subtitle">管理 Lineages 和系统设置</p>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="admin-grid">
        <div className="admin-card">
          <h3>✨ 创建新 Lineage</h3>
          <div className="create-form">
            <div className="form-group">
              <label>名称</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="输入名称..."
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>模板</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="form-select"
              >
                {templates.map(t => (
                  <option key={t.id} value={t.id}>{t.name} - {t.desc}</option>
                ))}
              </select>
            </div>
            <button
              className="create-btn"
              onClick={handleCreate}
              disabled={loading}
            >
              {loading ? '创建中...' : '创建'}
            </button>
          </div>
        </div>

        <div className="admin-card danger-card">
          <h3>⚠️ 危险操作</h3>
          <div className="danger-actions">
            <div className="danger-item">
              <div className="danger-info">
                <span className="danger-title">重置系统</span>
                <span className="danger-desc">清空所有数据，重新初始化</span>
              </div>
              <button
                className={`danger-btn ${confirmAction === 'reset' ? 'confirm' : ''}`}
                onClick={handleReset}
                disabled={loading}
              >
                {confirmAction === 'reset' ? '确认重置' : '重置'}
              </button>
            </div>
            <div className="danger-item">
              <div className="danger-info">
                <span className="danger-title">清空一切</span>
                <span className="danger-desc">不可恢复地删除所有 Lineages</span>
              </div>
              <button
                className={`danger-btn danger ${confirmAction === 'clear' ? 'confirm' : ''}`}
                onClick={handleClear}
                disabled={loading}
              >
                {confirmAction === 'clear' ? '确认清空' : '清空'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="lineages-section">
        <h3>📋 所有 Lineages ({lineages.length})</h3>
        <div className="lineages-list">
          {lineages.length === 0 ? (
            <div className="empty-lineages">暂无 Lineages</div>
          ) : (
            lineages.map(lineage => (
              <div key={lineage.id} className="lineage-item">
                <div className="lineage-info">
                  <span className="lineage-name">{lineage.id}</span>
                  <span className="lineage-status">{lineage.status}</span>
                </div>
                <div className="lineage-actions">
                  <button
                    className={`delete-btn ${confirmAction === lineage.id ? 'confirm' : ''}`}
                    onClick={() => handleDelete(lineage.id)}
                    disabled={loading}
                  >
                    {confirmAction === lineage.id ? '确认删除' : '删除'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
