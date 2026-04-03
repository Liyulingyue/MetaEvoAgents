import { useState, useEffect, useRef } from 'react';
import type { Lineage } from '../types';
import './Observer.css';

interface EventMessage {
  type: string;
  lineage_id: string;
  content: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

export function Observer() {
  const [lineages, setLineages] = useState<Lineage[]>([]);
  const [events, setEvents] = useState<EventMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const eventSourceRef = useRef<EventSource | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchLineages();
    connectToEvents();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const fetchLineages = async () => {
    try {
      const response = await fetch('http://localhost:8000/agent/lineages');
      if (response.ok) {
        const data = await response.json();
        setLineages(data);
      }
    } catch (err) {
      console.error('Failed to fetch lineages:', err);
    }
  };

  const connectToEvents = () => {
    const eventSource = new EventSource('http://localhost:8000/agent/events/subscribe');
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') return;

        setEvents(prev => {
          const newEvents = [...prev, data];
          if (newEvents.length > 200) {
            return newEvents.slice(-200);
          }
          return newEvents;
        });
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    };

    eventSource.onerror = () => {
      setConnected(false);
      setTimeout(connectToEvents, 3000);
    };
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'step': return '⚡';
      case 'tool': return '🔧';
      case 'thought': return '💭';
      case 'output': return '📤';
      case 'error': return '❌';
      case 'birth': return '✦';
      case 'death': return '✧';
      default: return '●';
    }
  };

  const getEventClass = (type: string) => {
    switch (type) {
      case 'step': return 'event-step';
      case 'tool': return 'event-tool';
      case 'thought': return 'event-thought';
      case 'output': return 'event-output';
      case 'error': return 'event-error';
      case 'birth': return 'event-birth';
      case 'death': return 'event-death';
      default: return '';
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const filteredEvents = filter === 'all'
    ? events
    : events.filter(e => e.lineage_id === filter);

  return (
    <div className="observer">
      <div className="observer-header">
        <div className="header-left">
          <h2>👁️ 实时观察</h2>
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {connected ? '已连接' : '已断开'}
          </div>
        </div>
        <div className="header-right">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">所有 Agent</option>
            {lineages.map(l => (
              <option key={l.id} value={l.id}>{l.id}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="events-container">
        {filteredEvents.length === 0 ? (
          <div className="empty-events">
            <span className="empty-icon">👁️</span>
            <p>暂无事件</p>
            <span>等待 Agent 活动...</span>
          </div>
        ) : (
          <div className="events-list">
            {filteredEvents.map((event, index) => (
              <div
                key={index}
                className={`event-item ${getEventClass(event.type)}`}
              >
                <div className="event-time">{formatTime(event.timestamp)}</div>
                <div className="event-icon">{getEventIcon(event.type)}</div>
                <div className="event-content">
                  <div className="event-header">
                    <span className="event-type">{event.type}</span>
                    <span className="event-lineage">{event.lineage_id}</span>
                  </div>
                  <div className="event-message">{event.content}</div>
                  {event.data && Object.keys(event.data).length > 0 && (
                    <pre className="event-data">{JSON.stringify(event.data, null, 2)}</pre>
                  )}
                </div>
              </div>
            ))}
            <div ref={eventsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
