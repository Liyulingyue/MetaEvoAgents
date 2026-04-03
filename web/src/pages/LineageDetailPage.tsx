import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { chatApi } from '../api';
import type { IntrospectResponse } from '../types';
import './LineageDetailPage.css';

interface LineageFile {
  name: string;
  size: number;
  modified: number;
}

type TabType = 'info' | 'files';

export function LineageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<IntrospectResponse | null>(null);
  const [files, setFiles] = useState<LineageFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<LineageFile | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [loadingFile, setLoadingFile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('info');

  useEffect(() => {
    if (id) {
      fetchData();
      fetchFiles();
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
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchFiles = async () => {
    if (!id) return;
    try {
      const response = await fetch(`http://localhost:8000/agent/lineages/${id}/files`);
      if (response.ok) {
        const result = await response.json();
        setFiles(result.files || []);
      }
    } catch (err) {
      console.error('Failed to fetch files:', err);
    }
  };

  const fetchFile = async (file: LineageFile) => {
    if (!id) return;
    setLoadingFile(true);
    setSelectedFile(file);
    try {
      const response = await fetch(`http://localhost:8000/agent/lineages/${id}/files/${file.name}`);
      if (response.ok) {
        const result = await response.json();
        setFileContent(result.content || '');
      } else {
        setFileContent('无法读取文件');
      }
    } catch {
      setFileContent('读取失败');
    } finally {
      setLoadingFile(false);
    }
  };

  const getStatusColor = (status: string | undefined) => {
    if (!status) return '#6b7280';
    const s = status.toLowerCase();
    switch (s) {
      case 'busy':
      case 'running': return '#eab308';
      case 'idle':
      case 'completed': return '#22c55e';
      case 'offline':
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.py')) return { icon: '🐍', color: '#3b82f6' };
    if (filename.endsWith('.md')) return { icon: '📝', color: '#22c55e' };
    if (filename.endsWith('.json')) return { icon: '📋', color: '#f59e0b' };
    if (filename.endsWith('.txt')) return { icon: '📄', color: '#6b7280' };
    if (filename.endsWith('.env')) return { icon: '🔐', color: '#ef4444' };
    if (filename.endsWith('.yaml') || filename.endsWith('.yml')) return { icon: '⚙️', color: '#8b5cf6' };
    if (filename.endsWith('.sh')) return { icon: '📜', color: '#14b8a6' };
    return { icon: '📄', color: '#6b7280' };
  };

  const getStatusDisplay = (status: string | undefined) => {
    if (!status) return '未知 (UNKNOWN)';
    const s = status.toLowerCase();
    if (s === 'idle') return '空闲 (IDLE)';
    if (s === 'busy') return '忙碌 (BUSY)';
    if (s === 'offline') return '离线 (OFFLINE)';
    return status.toUpperCase();
  };

  if (loading) {
    return (
      <div className="detail-page">
        <div className="loading-container">
          <div className="loading-orb"></div>
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="detail-page">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2>加载失败</h2>
          <p>{error || '未找到 Lineage'}</p>
          <Link to="/lineages" className="error-btn">← 返回列表</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <header className="detail-header">
        <Link to="/lineages" className="back-btn">
          <span>←</span>
          <span>返回列表</span>
        </Link>
        
        <div className="hero-section">
          <div className="hero-content">
            <div className="agent-avatar">
              <span className="avatar-icon">🧬</span>
              <div className="status-glow" style={{ background: getStatusColor(data.status) }}></div>
            </div>
            <div className="agent-info">
              <h1 className="agent-name">{data.id}</h1>
              <div className="agent-meta">
                {data.metadata?.generation && (
                  <span className="meta-badge">G{data.metadata.generation}</span>
                )}
                <span className="meta-badge status" style={{ background: `${getStatusColor(data.status)}20`, color: getStatusColor(data.status) }}>
                  {getStatusDisplay(data.status)}
                </span>
                {data.metadata?.uid && (
                  <span className="meta-badge uid">{data.metadata.uid}</span>
                )}
              </div>
            </div>
          </div>
          <div className="hero-decoration">
            <div className="deco-circle circle-1"></div>
            <div className="deco-circle circle-2"></div>
            <div className="deco-circle circle-3"></div>
          </div>
        </div>
      </header>

      <nav className="detail-nav">
        <button
          className={`nav-btn ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          <span className="nav-icon">📊</span>
          <span>信息概览</span>
        </button>
        <button
          className={`nav-btn ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          <span className="nav-icon">📁</span>
          <span>文件 ({files.length})</span>
        </button>
      </nav>

      <div className="detail-body">
        {activeTab === 'info' ? (
          <div className="info-grid">
            <div className="info-card instruction-card">
              <div className="card-header">
                <span className="card-icon">📜</span>
                <h3>指令</h3>
              </div>
              <pre className="card-content">{data.instruction || '(无指令)'}</pre>
            </div>

            <div className="info-card memory-card">
              <div className="card-header">
                <span className="card-icon">🧠</span>
                <h3>记忆</h3>
              </div>
              <pre className="card-content">{data.memory || '(无记忆)'}</pre>
            </div>

            <div className="info-card history-card">
              <div className="card-header">
                <span className="card-icon">📋</span>
                <h3>历史</h3>
                <span className="card-count">{(data.history || []).length} 条</span>
              </div>
              <div className="history-scroll">
                {(data.history || []).length === 0 ? (
                  <div className="empty-hint">暂无历史记录</div>
                ) : (
                  (data.history || []).slice(-10).reverse().map((entry, index) => (
                    <div key={index} className="history-item">
                      <div className="history-dot" style={{ background: getStatusColor(data.status) }}></div>
                      <div className="history-content">
                        <div className="history-meta">
                          <span className="history-role">{entry.role}</span>
                          <span className="history-time">{formatDate(entry.timestamp)}</span>
                        </div>
                        <p className="history-text">{entry.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="info-card meta-card">
              <div className="card-header">
                <span className="card-icon">⚙️</span>
                <h3>配置</h3>
              </div>
              <div className="meta-grid">
                {data.metadata && Object.entries(data.metadata).map(([key, value]) => (
                  <div key={key} className="meta-item">
                    <span className="meta-key">{key}</span>
                    <span className="meta-val">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="files-view">
            <div className="files-sidebar">
              <div className="files-header">
                <span>文件列表</span>
                <span className="files-count">{files.length} 个</span>
              </div>
              <div className="files-list">
                {files.length === 0 ? (
                  <div className="empty-hint">暂无文件</div>
                ) : (
                  files.map((file, index) => {
                    const { icon, color } = getFileIcon(file.name);
                    return (
                      <button
                        key={index}
                        className={`file-btn ${selectedFile?.name === file.name ? 'active' : ''}`}
                        onClick={() => fetchFile(file)}
                      >
                        <span className="file-icon" style={{ color }}>{icon}</span>
                        <div className="file-details">
                          <span className="file-name">{file.name}</span>
                          <span className="file-size">{formatFileSize(file.size)}</span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            <div className="files-preview">
              {selectedFile ? (
                <>
                  <div className="preview-header">
                    <span className="preview-icon">{getFileIcon(selectedFile.name).icon}</span>
                    <span className="preview-name">{selectedFile.name}</span>
                    <span className="preview-size">{formatFileSize(selectedFile.size)}</span>
                  </div>
                  <div className="preview-body">
                    {loadingFile ? (
                      <div className="preview-loading">
                        <div className="loading-dots">
                          <span></span><span></span><span></span>
                        </div>
                      </div>
                    ) : (
                      <pre className="preview-code">{fileContent}</pre>
                    )}
                  </div>
                </>
              ) : (
                <div className="preview-empty">
                  <span className="empty-icon">👆</span>
                  <p>选择一个文件查看内容</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
