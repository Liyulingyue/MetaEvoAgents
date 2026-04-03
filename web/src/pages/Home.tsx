import { useState, useEffect } from 'react';
import { ChatPanel } from '../components/ChatPanel';
import type { Lineage } from '../types';

export function Home() {
  const [lineages, setLineages] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    fetchLineages();
  }, []);

  const fetchLineages = async () => {
    try {
      const response = await fetch('http://localhost:8000/agent/lineages');
      if (response.ok) {
        const data = await response.json();
        setLineages(data.map((l: Lineage) => ({ id: l.id, name: l.id })));
      }
    } catch {
      setLineages([{ id: 'Lineage-01', name: 'Lineage-01' }]);
    }
  };

  return (
    <div className="home-page">
      <div className="page-header">
        <h1>◈ 对话</h1>
        <p className="page-subtitle">与 AI Agent 畅所欲言</p>
      </div>
      <ChatPanel lineages={lineages} />
    </div>
  );
}
