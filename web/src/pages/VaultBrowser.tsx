import { useState, useEffect, useRef } from 'react';
import './VaultBrowser.css';

interface ZoneFile {
  name: string;
  size: number;
  modified: number;
}

interface Zone {
  id: string;
  name: string;
  desc: string;
  icon: string;
  path: string;
  files: ZoneFile[];
}

interface Lineage {
  id: string;
  name: string;
}

interface VaultFile {
  name: string;
  size: number;
  modified: number;
}

export function VaultBrowser() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [lineages, setLineages] = useState<Lineage[]>([]);
  const [selectedZone, setSelectedZone] = useState<string>('altar');
  const [selectedLineage, setSelectedLineage] = useState<string>('');
  const [vaultFiles, setVaultFiles] = useState<VaultFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchZones();
    fetchLineages();
  }, []);

  useEffect(() => {
    if (selectedZone === 'vault' && selectedLineage) {
      fetchVaultFiles(selectedLineage);
    } else {
      fetchZoneFiles(selectedZone);
    }
  }, [selectedZone, selectedLineage]);

  const fetchZones = async () => {
    try {
      const response = await fetch('http://localhost:8000/agent/files/zones');
      if (response.ok) {
        const data = await response.json();
        setZones(data.zones);
      }
    } catch (err) {
      console.error('Failed to fetch zones:', err);
    }
  };

  const fetchLineages = async () => {
    try {
      const response = await fetch('http://localhost:8000/agent/lineages');
      if (response.ok) {
        const data = await response.json();
        setLineages(data);
        if (data.length > 0) {
          setSelectedLineage(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch lineages:', err);
    }
  };

  const fetchZoneFiles = async (zone: string) => {
    setLoading(true);
    setSelectedFile(null);
    setFileContent('');
    try {
      const response = await fetch(`http://localhost:8000/agent/files/${zone}`);
      if (response.ok) {
        const data = await response.json();
        if (zone === 'vault') {
          setVaultFiles(data.files || []);
        } else {
          setZones(prev => prev.map(z =>
            z.id === zone ? { ...z, files: data.files || [] } : z
          ));
        }
      }
    } catch (err) {
      console.error('Failed to fetch zone files:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchVaultFiles = async (lineageId: string) => {
    setLoading(true);
    setSelectedFile(null);
    setFileContent('');
    try {
      const response = await fetch(`http://localhost:8000/agent/vault/${lineageId}`);
      if (response.ok) {
        const data = await response.json();
        setVaultFiles(data.files || []);
      }
    } catch (err) {
      console.error('Failed to fetch vault files:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFile = async (zone: string, filePath: string) => {
    setLoadingFile(true);
    setSelectedFile(filePath);
    try {
      const url = zone === 'vault'
        ? `/agent/vault/${selectedLineage}/${filePath}`
        : `/agent/files/${zone}/${filePath}`;
      const response = await fetch(`http://localhost:8000${url}`);
      if (response.ok) {
        const data = await response.json();
        setFileContent(data.content || '');
      } else {
        setFileContent('无法加载文件内容');
      }
    } catch {
      setFileContent('加载文件失败');
    } finally {
      setLoadingFile(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadMessage('');

    const isAltar = selectedZone === 'altar';

    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const url = isAltar
          ? 'http://localhost:8000/agent/files/altar/upload'
          : `http://localhost:8000/agent/files/vault/${selectedLineage}/upload`;

        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (response.ok) {
          setUploadMessage(prev => prev + `✓ ${data.message}\n`);
        } else {
          setUploadMessage(prev => prev + `✗ ${data.detail}\n`);
        }
      } catch (err) {
        setUploadMessage(prev => prev + `✗ 上传失败\n`);
      }
    }

    setUploading(false);

    // 刷新文件列表
    if (isAltar) {
      fetchZoneFiles('altar');
    } else if (selectedLineage) {
      fetchVaultFiles(selectedLineage);
    }

    // 清空 input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const currentZone = zones.find(z => z.id === selectedZone);
  const displayFiles = selectedZone === 'vault' ? vaultFiles : (currentZone?.files || []);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const canUpload = selectedZone === 'altar' || (selectedZone === 'vault' && selectedLineage);

  return (
    <div className="vault-browser">
      <div className="vault-header">
        <h2>📁 文件区</h2>
        <p className="vault-subtitle">浏览、上传和管理所有文件</p>
      </div>

      <div className="zone-tabs">
        {zones.map(zone => (
          <button
            key={zone.id}
            className={`zone-tab ${selectedZone === zone.id ? 'active' : ''}`}
            onClick={() => setSelectedZone(zone.id)}
          >
            <span className="zone-icon">{zone.icon}</span>
            <span className="zone-name">{zone.name}</span>
            <span className="zone-count">{zone.files?.length || 0}</span>
          </button>
        ))}
      </div>

      <div className="vault-controls">
        {selectedZone === 'vault' && (
          <div className="lineage-selector-bar">
            <label>选择 Agent:</label>
            <select
              value={selectedLineage}
              onChange={(e) => setSelectedLineage(e.target.value)}
              className="lineage-select"
            >
              {lineages.map(l => (
                <option key={l.id} value={l.id}>{l.id}</option>
              ))}
            </select>
          </div>
        )}

        {canUpload && (
          <div className="upload-area">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleUpload}
              disabled={uploading}
              className="upload-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="upload-btn">
              {uploading ? '上传中...' : '📤 上传文件'}
            </label>
            {uploadMessage && (
              <div className="upload-message">
                {uploadMessage.split('\n').map((msg, i) => (
                  <div key={i}>{msg}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="vault-layout">
        <div className="vault-sidebar">
          <div className="zone-info">
            <h3>{currentZone?.icon} {currentZone?.name}</h3>
            <p>{currentZone?.desc}</p>
          </div>

          <div className="file-list">
            {loading ? (
              <div className="loading">
                <div className="loading-spinner"></div>
                <span>加载中...</span>
              </div>
            ) : displayFiles.length ? (
              displayFiles.map((file: ZoneFile, index: number) => (
                <div
                  key={index}
                  className={`file-item ${selectedFile === file.name ? 'selected' : ''}`}
                >
                  <div
                    className="file-info"
                    onClick={() => fetchFile(selectedZone, file.name)}
                  >
                    <span className="file-icon">📄</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{formatFileSize(file.size)}</span>
                  </div>
                  <button
                    className="file-download-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      const url = selectedZone === 'altar'
                        ? `http://localhost:8000/agent/files/altar/${encodeURIComponent(file.name)}`
                        : `http://localhost:8000/agent/files/vault/${selectedLineage}/${encodeURIComponent(file.name)}`;
                      window.open(url, '_blank');
                    }}
                    title="下载"
                  >
                    ⬇
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-list">
                <span>📂</span>
                <p>暂无文件</p>
                {canUpload && <p className="hint">点击上方按钮上传</p>}
              </div>
            )}
          </div>
        </div>

        <div className="vault-content">
          {selectedFile ? (
            <>
              <div className="file-header">
                <div className="file-info">
                  <span className="file-title">📄 {selectedFile}</span>
                </div>
              </div>
              <div className="file-viewer">
                {loadingFile ? (
                  <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>加载中...</span>
                  </div>
                ) : (
                  <pre className="file-content">{fileContent}</pre>
                )}
              </div>
            </>
          ) : (
            <div className="no-file-selected">
              <span className="empty-icon">📄</span>
              <p>选择文件查看内容</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
