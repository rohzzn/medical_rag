import { getSession } from 'next-auth/react';

// API base URL for client-side requests
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Generic fetch function with authorization
 */
async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  console.log(`Making API request to: ${API_BASE_URL}${endpoint}`);
  
  const session = await getSession();
  
  if (!session?.accessToken) {
    console.error('No access token available');
    throw new Error('No access token available');
  }
  
  console.log(`Using token: ${session.accessToken.slice(0, 10)}...`);
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.accessToken}`,
    ...options.headers,
  };
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
    
    console.log(`Response status: ${response.status}`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error(`API error: ${JSON.stringify(error)}`);
      throw new Error(error.detail || `API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`Response data: ${JSON.stringify(data).slice(0, 200)}...`);
    return data;
  } catch (error) {
    console.error(`Fetch error: ${error}`);
    throw error;
  }
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