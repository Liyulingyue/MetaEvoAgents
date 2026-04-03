import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { chatApi } from '../api';
import type { IntrospectResponse, Lineage } from '../types';
import './LineageList.css';

interface VaultFile {
  name: string;
  size: number;
  modified: number;
}

interface VaultData {
  lineage_id: string;
  path: string;
  files: VaultFile[];
}

interface LineageListProps {
  lineages: Lineage[];
  onRefresh: () => void;
}

export function LineageList({ lineages, onRefresh }: LineageListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, IntrospectResponse>>({});
  const [vaults, setVaults] = useState<Record<string, VaultData>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedId && !details[selectedId]) {
      fetchDetail(selectedId);
    }
    if (selectedId && !vaults[selectedId]) {
      fetchVault(selectedId);
    }
  }, [selectedId]);

  const fetchDetail = async (lineageId: string) => {
    setLoading(true);
    try {
      const data = await chatApi.introspect(lineageId);
      setDetails(prev => ({ ...prev, [lineageId]: data }));
    } catch (error) {
      console.error('Failed to fetch lineage detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchVault = async (lineageId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/agent/vault/${lineageId}`);
      if (response.ok) {
        const data = await response.json();
        setVaults(prev => ({ ...prev, [lineageId]: data }));
      }
    } catch (error) {
      console.error('Failed to fetch vault:', error);
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

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="lineage-list">
      <div className="list-header">
        <h2>◉ Lineages</h2>
        <button className="refresh-btn" onClick={onRefresh}>
          ⟳ 刷新
        </button>
      </div>

      <div className="list-container">
        <div className="lineage-cards">
          {lineages.length === 0 ? (
            <div className="empty-lineages">
              <p>暂无 Lineages</p>
              <span>创建第一个 Lineage 开始演化</span>
            </div>
          ) : (
            lineages.map(lineage => (
              <div
                key={lineage.id}
                className={`lineage-card ${selectedId === lineage.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(lineage.id)}
              >
                <div className="card-header">
                  <span className="card-id">{lineage.id}</span>
                  <span className={`card-status ${getStatusClass(lineage.status)}`}>
                    {lineage.status}
                  </span>
                </div>
                <div className="card-body">
                  {lineage.metadata?.name && (
                    <div className="card-name">{lineage.metadata.name}</div>
                  )}
                  <div className="card-meta">
                    {lineage.metadata?.generation && (
                      <span>代: {lineage.metadata.generation}</span>
                    )}
                    <span>创建: {formatDate(lineage.created_at)}</span>
                  </div>
                </div>
                <div className="card-footer">
                  <Link
                    to={`/lineages/${lineage.id}`}
                    className="card-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    查看详情 →
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>

        {selectedId && details[selectedId] && (
          <div className="lineage-detail">
            <div className="detail-header">
              <h3>{details[selectedId].id}</h3>
              <span className={`detail-status ${getStatusClass(details[selectedId].status)}`}>
                {details[selectedId].status}
              </span>
            </div>

            <div className="detail-section">
              <h4>指令 (Instruction)</h4>
              <pre className="detail-code">{details[selectedId].instruction}</pre>
            </div>

            <div className="detail-section">
              <h4>记忆 (Memory)</h4>
              <pre className="detail-content">{details[selectedId].memory || ''}</pre>
            </div>

            <div className="detail-section">
              <h4>历史记录 ({(details[selectedId].history || []).length})</h4>
              <div className="history-list">
                {(details[selectedId].history || []).slice(-10).reverse().map((entry: { role: string; timestamp: number; content: string }, index: number) => (
                  <div key={index} className="history-item">
                    <span className="history-role">{entry.role}</span>
                    <span className="history-time">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                    <div className="history-content">{entry.content}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h4>元数据</h4>
              <div className="metadata-grid">
                {details[selectedId].metadata && Object.entries(details[selectedId].metadata).map(([key, value]: [string, unknown]) => (
                  <div key={key} className="metadata-item">
                    <span className="metadata-key">{key}</span>
                    <span className="metadata-value">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h4>📁 Vault ({vaults[selectedId]?.files?.length || 0} 文件)</h4>
              {vaults[selectedId]?.files?.length ? (
                <div className="vault-files">
                  {vaults[selectedId].files.map((file: VaultFile, index: number) => (
                    <div key={index} className="vault-file">
                      <span className="file-icon">📄</span>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-text">暂无文件</p>
              )}
            </div>
          </div>
        )}

        {selectedId && loading && (
          <div className="detail-loading">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        )}
      </div>
    </div>
  );
}
