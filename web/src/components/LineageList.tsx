import { Link } from 'react-router-dom';
import type { Lineage } from '../types';
import './LineageList.css';

interface LineageListProps {
  lineages: Lineage[];
  onRefresh: () => void;
}

export function LineageList({ lineages, onRefresh }: LineageListProps) {
  const getStatusClass = (status: string) => {
    const s = status.toLowerCase();
    switch (s) {
      case 'busy':
      case 'running': return 'status-running';
      case 'idle':
      case 'completed': return 'status-completed';
      case 'offline':
      case 'error': return 'status-error';
      default: return 'status-idle';
    }
  };

  const getStatusLabel = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'idle') return '空闲';
    if (s === 'busy') return '忙碌';
    if (s === 'offline') return '离线';
    return status.toUpperCase();
  };

  const formatDate = (timestamp: number) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleDateString('zh-CN', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="lineage-list">
      <div className="list-header">
        <div className="header-left">
          <h2>◉ Lineages</h2>
          <span className="lineage-count">{lineages.length} 个智能体</span>
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          刷新
          <span className="refresh-icon">↻</span>
        </button>
      </div>

      <div className="lineage-grid">
        {lineages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">◉</div>
            <h3>暂无智能体</h3>
            <p>创建第一个 Lineage 开始演化</p>
            <Link to="/admin" className="create-link">
              前往创建 →
            </Link>
          </div>
        ) : (
          lineages.map((lineage, index) => (
            <Link
              key={lineage.id}
              to={`/lineages/${lineage.id}`}
              className="lineage-card"
            >
              <div className="card-glow"></div>
              <div className="card-content">
                <div className="card-top">
                  <span className={`status-dot ${getStatusClass(lineage.status)}`}></span>
                  <span className="card-index">#{String(index + 1).padStart(2, '0')}</span>
                </div>

                <div className="card-main">
                  <h3 className="card-name">{lineage.id}</h3>
                  {lineage.metadata?.name && (
                    <p className="card-alias">{lineage.metadata.name}</p>
                  )}
                </div>

                <div className="card-meta">
                  <div className="meta-item">
                    <span className="meta-label">世代</span>
                    <span className="meta-value">{lineage.metadata?.generation || 1}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">创建</span>
                    <span className="meta-value">{formatDate(lineage.created_at)}</span>
                  </div>
                </div>

                <div className="card-footer">
                  <span className="card-status">{getStatusLabel(lineage.status)}</span>
                  <span className="card-arrow">→</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
