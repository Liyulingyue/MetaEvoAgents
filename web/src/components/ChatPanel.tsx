import { useState, useRef, useEffect } from 'react';
import type { ChatMessage, ChatResponse, Step } from '../types';
import './ChatPanel.css';

interface Lineage {
  id: string;
  name: string;
}

interface ChatPanelProps {
  lineages: Lineage[];
}

type RunType = 'SYNC' | 'ASYNC';
type DispatchMode = 'random' | 'latest';
type SendMode = 'auto' | 'direct' | 'broadcast';

const SESSION_FILE = 'chat_session.json';
const API_BASE = 'http://localhost:8000/agent';

async function loadSession(): Promise<ChatMessage[]> {
  try {
    const resp = await fetch(`${API_BASE}/chat-session`);
    if (resp.ok) {
      const data = await resp.json();
      return (data.messages || []).map((m: any) => ({
        id: m.id || crypto.randomUUID(),
        role: m.role,
        content: m.content,
        timestamp: m.timestamp || Date.now(),
      }));
    }
  } catch {}
  return [];
}

async function saveSession(msgs: ChatMessage[]): Promise<void> {
  try {
    await fetch(`${API_BASE}/chat-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: msgs }),
    });
  } catch {}
}

export function ChatPanel({ lineages }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<ChatResponse | null>(null);
  const [lineageId, setLineageId] = useState('auto');
  const [pinnedLineage, setPinnedLineage] = useState<string | null>(null);
  const [maxSteps, setMaxSteps] = useState(10);
  const [runType, setRunType] = useState<RunType>('SYNC');
  const [dispatchMode, setDispatchMode] = useState<DispatchMode>('random');
  const [sendMode, setSendMode] = useState<SendMode>('auto');
  const [showSettings, setShowSettings] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

  useEffect(() => {
    loadSession().then(msgs => {
      setMessages(msgs);
      setLoaded(true);
    });
  }, []);

  useEffect(() => {
    if (sendMode === 'direct' && lineageId !== 'auto') {
      fetchHistory(lineageId);
    }
  }, [sendMode, lineageId]);

  const appendMessage = (msg: ChatMessage) => {
    setMessages(prev => {
      const next = [...prev, msg];
      saveSession(next);
      return next;
    });
  };

  const fetchHistory = async (lid: string) => {
    setIsLoading(true);
    try {
      const resp = await fetch(`http://localhost:8000/agent/history/${lid}`);
      if (resp.ok) {
        const data = await resp.json();
        const historyMessages: ChatMessage[] = data.history
          .filter((m: any) => m.role === 'user' || m.role === 'assistant')
          .map((m: any) => ({
            id: crypto.randomUUID(),
            role: m.role,
            content: m.content || (m.tool_calls ? '调用工具中...' : ''),
            timestamp: Date.now(),
          }));
        setMessages(historyMessages);
        saveSession(historyMessages);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: Date.now(),
    };

    appendMessage(userMessage);
    setInput('');
    setIsLoading(true);
    setCurrentResponse(null);

    try {
      let endpoint = '/agent/chat';
      let requestBody: Record<string, unknown> = {
        message: input,
        lineage_id: lineageId,
        max_steps: maxSteps,
        run_type: runType,
        dispatch_mode: dispatchMode,
      };

      if (sendMode === 'broadcast') {
        endpoint = '/agent/broadcast';
      }

      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '请求失败');
      }

      if (data.status === 'async_started') {
        if (data.lineage_id) setPinnedLineage(data.lineage_id);
        appendMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⏳ [ASYNC] 任务已在后台启动\n子民 ${data.lineage_id} 正在执行中...`,
          timestamp: Date.now(),
        });
      } else if (data.status === 'broadcast_ok') {
        const coordinator = data.coordinator || data.lineage_ids?.[0] || '未知';
        if (data.results && data.results.length > 0) {
          const result = data.results[0];
          if (result.status === 'ok' && result.output) {
            if (data.coordinator) setPinnedLineage(data.coordinator);
            setCurrentResponse({} as ChatResponse);
            appendMessage({
              id: crypto.randomUUID(),
              role: 'assistant',
              content: result.output,
              timestamp: Date.now(),
            });
          } else if (result.status === 'error') {
            appendMessage({
              id: crypto.randomUUID(),
              role: 'assistant',
              content: `❌ ${result.error}`,
              timestamp: Date.now(),
            });
          } else {
            appendMessage({
              id: crypto.randomUUID(),
              role: 'assistant',
              content: `📢 任务已分配给 ${coordinator} 协调执行${data.message ? '\n' + data.message : ''}`,
              timestamp: Date.now(),
            });
          }
        } else {
          appendMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `📢 任务已分配给 ${coordinator} 协调执行${data.message ? '\n' + data.message : ''}`,
            timestamp: Date.now(),
          });
        }
      } else {
        if (data.lineage_id) setPinnedLineage(data.lineage_id);
        setCurrentResponse(data);
        appendMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.final_output || data.message || '任务完成',
          timestamp: Date.now(),
        });
      }
    } catch (error) {
      appendMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `❌ 错误: ${error instanceof Error ? error.message : '请求失败'}`,
        timestamp: Date.now(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNew = () => {
    setPinnedLineage(null);
    setSendMode('auto');
    setLineageId('auto');
    setMessages([]);
    setCurrentResponse(null);
    saveSession([]);
  };

  const getModeIcon = () => {
    switch (sendMode) {
      case 'broadcast': return '📢';
      case 'direct': return '◈';
      default: return '◎';
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title">
          <span className="title-icon">{getModeIcon()}</span>
          <h2>对话</h2>
          {pinnedLineage && (
            <span className="pinned-lineage">
              📌 {pinnedLineage}
            </span>
          )}
        </div>
        <div className="chat-actions">
          <button
            className="icon-btn new-btn"
            onClick={handleNew}
            title="新对话 (New)"
          >
            ✨ 新对话
          </button>
          <button
            className="icon-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="设置"
          >
            ⚙
          </button>
        </div>
      </div>

      <div className="chat-config">
        <div className="config-row">
          <div className="send-modes">
            <button
              className={`mode-btn ${sendMode === 'auto' ? 'active' : ''}`}
              onClick={() => setSendMode('auto')}
            >
              ◎ 自动分配
            </button>
            <button
              className={`mode-btn ${sendMode === 'direct' ? 'active' : ''}`}
              onClick={() => setSendMode('direct')}
            >
              ◈ 指定
            </button>
            <button
              className={`mode-btn ${sendMode === 'broadcast' ? 'active' : ''}`}
              onClick={() => setSendMode('broadcast')}
            >
              📢 发布任务
            </button>
          </div>
          {sendMode === 'direct' && (
            <label className="config-label">
              <select
                value={lineageId}
                onChange={(e) => setLineageId(e.target.value)}
                className="config-select"
              >
                {lineages.map(l => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </label>
          )}
        </div>

        {showSettings && (
          <div className="config-advanced">
            <div className="config-row">
              {sendMode === 'auto' && (
                <label className="config-label">
                  <span>分配策略</span>
                  <select
                    value={dispatchMode}
                    onChange={(e) => setDispatchMode(e.target.value as DispatchMode)}
                    className="config-select"
                  >
                    <option value="random">随机分配</option>
                    <option value="latest">最近创建</option>
                  </select>
                </label>
              )}

              <label className="config-label">
                <span>运行模式</span>
                <select
                  value={runType}
                  onChange={(e) => setRunType(e.target.value as RunType)}
                  className="config-select"
                >
                  <option value="SYNC">🔄 同步等待</option>
                  <option value="ASYNC">⚡ 异步后台</option>
                </select>
              </label>

              <label className="config-label">
                <span>最大步数</span>
                <input
                  type="number"
                  value={maxSteps}
                  onChange={(e) => setMaxSteps(parseInt(e.target.value) || 10)}
                  min={1}
                  max={100}
                  className="config-input"
                />
              </label>
            </div>
          </div>
        )}
      </div>

      <div className="chat-messages">
        {!loaded && messages.length === 0 && (
          <div className="empty-state">
            <div className="loading-spinner"></div>
            <span>加载对话记录...</span>
          </div>
        )}

        {loaded && messages.length === 0 && !currentResponse && (
          <div className="empty-state">
            <div className="empty-icon">◎</div>
            <p>开始与 AI Agent 对话</p>
            <span>使用不同的模式与宗族互动</span>
            <div className="mode-hints">
              <div className="hint-item">
                <span className="hint-icon">◎</span>
                <span>自动分配 - 系统自动选择空闲宗族</span>
              </div>
              <div className="hint-item">
                <span className="hint-icon">◈</span>
                <span>指定 - 手动选择特定宗族</span>
              </div>
              <div className="hint-item">
                <span className="hint-icon">📢</span>
                <span>发布任务 - 直达所有宗族</span>
              </div>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '◉' : '◈'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              <div className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {currentResponse && (
          <div className="response-steps">
            <div className="steps-header">
              <span className="steps-icon">⚙</span>
              <span>执行步骤 ({currentResponse.steps?.length || 0})</span>
              {currentResponse.lineage_id && (
                <span className="steps-lineage">→ {currentResponse.lineage_id}</span>
              )}
            </div>
            <div className="steps-list">
              {currentResponse.steps?.map((step: Step, index: number) => (
                <div key={index} className="step-item">
                  <div className="step-number">#{step.step}</div>
                  <div className="step-content">
                    {step.thought && (
                      <div className="step-thought">
                        <span className="step-label">思考:</span> {step.thought}
                      </div>
                    )}
                    <div className="step-action">
                      <span className="step-label">动作:</span> {step.action}
                    </div>
                    <div className="step-observation">
                      <span className="step-label">观察:</span> {step.observation}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="loading-spinner"></div>
            <span>Agent 正在思考...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            sendMode === 'broadcast'
              ? '发布任务给所有宗族...'
              : '输入你的消息...'
          }
          className="chat-input"
          rows={1}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isLoading}
        >
          {isLoading ? '◐' : '◀'}
        </button>
      </form>
    </div>
  );
}
