import { useState, useCallback } from 'react';
import type { ChatMessage, Lineage, ChatResponse } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  currentResponse: ChatResponse | null;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    currentResponse: null,
    error: null,
  });

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));
    return newMessage;
  }, []);

  const setLoading = useCallback((isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading }));
  }, []);

  const setResponse = useCallback((response: ChatResponse | null) => {
    setState(prev => ({ ...prev, currentResponse: response }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const clearChat = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      currentResponse: null,
      error: null,
    });
  }, []);

  return {
    ...state,
    addMessage,
    setLoading,
    setResponse,
    setError,
    clearChat,
  };
}

export function useLineages() {
  const [lineages, setLineages] = useState<Lineage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLineages = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/agent/lineages');
      if (response.ok) {
        const data = await response.json();
        setLineages(data);
      }
    } catch (err) {
      setError('Failed to fetch lineages');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addLineage = useCallback((lineage: Lineage) => {
    setLineages(prev => {
      const exists = prev.find(l => l.id === lineage.id);
      if (exists) {
        return prev.map(l => l.id === lineage.id ? lineage : l);
      }
      return [...prev, lineage];
    });
  }, []);

  const updateLineage = useCallback((id: string, updates: Partial<Lineage>) => {
    setLineages(prev => prev.map(l => 
      l.id === id ? { ...l, ...updates } : l
    ));
  }, []);

  return {
    lineages,
    isLoading,
    error,
    fetchLineages,
    addLineage,
    updateLineage,
  };
}
