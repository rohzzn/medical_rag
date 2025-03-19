import { getSession } from 'next-auth/react';

// API base URL for client-side requests
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Determine if we're running on the server
const isServer = typeof window === 'undefined';

/**
 * Generic fetch function with authorization
 */
async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const session = await getSession();
  
  if (!session?.accessToken) {
    throw new Error('No access token available');
  }
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.accessToken}`,
    ...options.headers,
  };
  
  // Use the appropriate base URL depending on where we're running
  const baseUrl = API_BASE_URL;
  
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API request failed with status ${response.status}`);
  }
  
  return response.json();
}

/**
 * User API
 */
export const userApi = {
  getCurrentUser: () => fetchWithAuth('/users/me'),
  updateUser: (userData: any) => fetchWithAuth('/users/me', {
    method: 'PUT',
    body: JSON.stringify(userData),
  }),
};

/**
 * Conversation API
 */
export const conversationApi = {
  getAllConversations: () => fetchWithAuth('/queries/conversations'),
  getConversation: (id: number) => fetchWithAuth(`/queries/conversations/${id}`),
  createConversation: (title?: string) => fetchWithAuth('/queries/conversations', {
    method: 'POST',
    body: JSON.stringify({ title }),
  }),
  getMessages: (conversationId: number) => 
    fetchWithAuth(`/queries/conversations/${conversationId}/messages`),
};

/**
 * Query API
 */
export const queryApi = {
  submitQuery: (query: string, conversationId?: number) => 
    fetchWithAuth('/queries/query', {
      method: 'POST',
      body: JSON.stringify({ query, conversation_id: conversationId }),
    }),
};

/**
 * Types
 */
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: Source[];
}

export interface Source {
  source_path: string;
  source_name: string;
}

export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface QueryResult {
  answer: string;
  sources: Source[];
  conversation_id: number;
}