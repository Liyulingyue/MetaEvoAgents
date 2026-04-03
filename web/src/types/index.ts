export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface ChatRequest {
  message: string;
  lineage_id: string;
  max_steps: number;
  run_type?: 'SYNC' | 'ASYNC';
  dispatch_mode?: 'random' | 'latest';
}

export interface ChatResponse {
  session_id?: string;
  steps?: Step[];
  final_output?: string;
  lineage_id?: string;
  status?: string;
  message?: string;
  thread_name?: string;
}

export interface Step {
  step: number;
  action: string;
  observation: string;
  thought?: string;
}

export interface Lineage {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  created_at: number;
  instruction?: string;
  metadata?: LineageMetadata;
}

export interface LineageMetadata {
  name?: string;
  uid?: string;
  generation?: number;
  parent_id?: string;
  traits?: string[];
  birth_date?: string;
  last_active?: string;
}

export interface IntrospectResponse {
  id: string;
  status: string;
  instruction: string;
  memory: string;
  history: HistoryEntry[];
  metadata: LineageMetadata;
}

export interface HistoryEntry {
  role: string;
  content: string;
  timestamp: number;
}

export interface WorldLog {
  events: WorldEvent[];
}

export interface WorldEvent {
  type: string;
  lineage_id: string;
  content: string;
  timestamp: number;
}
