import { useState, useEffect } from 'react';
import { LineageList } from '../components/LineageList';
import type { Lineage } from '../types';

export function Lineages() {
  const [lineages, setLineages] = useState<Lineage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLineages();
  }, []);

  const fetchLineages = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/agent/lineages');
      if (response.ok) {
        const data = await response.json();
        setLineages(data);
      }
    } catch {
      setLineages([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lineages-page">
      <div className="page-header">
        <h1>◉ 宗族</h1>
        <p className="page-subtitle">管理所有 AI Agent 实体</p>
      </div>
      {loading ? (
        <div className="page-loading">
          <div className="loading-spinner"></div>
          <span>加载中...</span>
        </div>
      ) : (
        <LineageList lineages={lineages} onRefresh={fetchLineages} />
      )}
    </div>
  );
}
