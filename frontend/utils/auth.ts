import { signIn } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface RegisterFormData {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginFormData {
  email: string;
  password: string;
}

/**
 * Register a new user
 */
export async function registerUser(userData: RegisterFormData): Promise<any> {
  console.log(`Registering user with API at ${API_BASE_URL}/auth/register`);
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Registration failed with status ${response.status}`);
  }
  
  return response.json();
}

/**
 * Login user using NextAuth
 */
export async function loginUser(credentials: LoginFormData): Promise<boolean> {
  console.log(`Logging in user with NextAuth`);
  const result = await signIn('credentials', {
    redirect: false,
    email: credentials.email,
    password: credentials.password,
  });
  
  if (result?.error) {
    console.error(`Login error: ${result.error}`);
    throw new Error(result.error);
  }
  
  return result?.ok || false;
}