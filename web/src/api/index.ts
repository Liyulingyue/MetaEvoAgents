import axios from 'axios';
import type { ChatRequest, ChatResponse, IntrospectResponse, Lineage } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
});

export const chatApi = {
  sendMessage: async (req: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/agent/chat', req);
    return response.data;
  },

  introspect: async (lineageId: string): Promise<IntrospectResponse> => {
    const response = await api.get<IntrospectResponse>(`/agent/introspect/${lineageId}`);
    return response.data;
  },
};

export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const response = await api.get<{ status: string }>('/health');
    return response.data;
  },
};

export const fetchLineages = async (): Promise<Lineage[]> => {
  try {
    const response = await api.get<Lineage[]>('/agent/lineages');
    return response.data;
  } catch {
    return [];
  }
};

export default api;
