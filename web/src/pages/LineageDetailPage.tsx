import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { chatApi } from '../api';
import type { IntrospectResponse } from '../types';
import './LineageDetailPage.css';

export function LineageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<IntrospectResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'instruction' | 'memory' | 'history'>('instruction');

  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id]);

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await chatApi.introspect(id);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lineage');
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'running': return 'status-running';
      case 'completed': return 'status-completed';
      case 'error': return 'status-error';
      default: return 'status-idle';
    }
  };

  if (loading) {
    return (
      <div className="lineage-detail-page">
        <div className="page-loading">
          <div className="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="lineage-detail-page">
        <div className="page-error">
          <h2>加载失败</h2>
          <p>{error || '未找到 Lineage'}</p>
          <Link to="/lineages" className="back-link">← 返回列表</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="lineage-detail-page">
      <div className="page-header">
        <Link to="/lineages" className="back-link">← 返回列表</Link>
        <div className="header-content">
          <h1>◉ {data.id}</h1>
          <span className={`status-badge ${getStatusClass(data.status)}`}>
            {data.status}
          </span>
        </div>
      </div>

      <div className="metadata-section">
        <h3>元数据</h3>
        <div className="metadata-grid">
          {data.metadata && Object.entries(data.metadata).map(([key, value]) => (
            <div key={key} className="metadata-item">
              <span className="metadata-key">{key}</span>
              <span className="metadata-value">{String(value)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'instruction' ? 'active' : ''}`}
          onClick={() => setActiveTab('instruction')}
        >
          指令
        </button>
        <button
          className={`tab ${activeTab === 'memory' ? 'active' : ''}`}
          onClick={() => setActiveTab('memory')}
        >
          记忆
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          历史 ({data.history.length})
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'instruction' && (
          <div className="content-section">
            <pre className="code-block">{data.instruction}</pre>
          </div>
        )}

        {activeTab === 'memory' && (
          <div className="content-section">
            <pre className="code-block">{data.memory}</pre>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="content-section">
            <div className="history-list">
              {data.history.length === 0 ? (
                <p className="empty-text">暂无历史记录</p>
              ) : (
                data.history.map((entry, index) => (
                  <div key={index} className="history-entry">
                    <div className="entry-header">
                      <span className="entry-role">{entry.role}</span>
                      <span className="entry-time">
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="entry-content">{entry.content}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
