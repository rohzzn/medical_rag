import NextAuth, { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { JWT } from 'next-auth/jwt';

// Extend the built-in types
declare module "next-auth" {
  interface User {
    id: string;
    email: string;
    name?: string;
    accessToken: string;
  }
  
  interface Session {
    accessToken: string;
    user: {
      id: string;
      email: string;
      name?: string;
    }
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken: string;
    id: string;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
// For server-side API calls when running in Docker, we need to use the service name
const SERVER_API_URL = process.env.SERVER_API_URL || 'http://backend:8000/api/v1';

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        
        try {
          // Get token from API
          console.log(`Sending auth request to ${SERVER_API_URL}/auth/login`);
          const response = await fetch(`${SERVER_API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
              username: credentials.email,
              password: credentials.password,
            }),
          });
          
          if (!response.ok) {
            console.error(`Auth error: ${response.status} ${response.statusText}`);
            return null;
          }
          
          const tokenData = await response.json();
          
          // Get user data
          console.log(`Getting user data from ${SERVER_API_URL}/users/me`);
          const userResponse = await fetch(`${SERVER_API_URL}/users/me`, {
            headers: {
              'Authorization': `Bearer ${tokenData.access_token}`,
            },
          });
          
          if (!userResponse.ok) {
            console.error(`User data error: ${userResponse.status} ${userResponse.statusText}`);
            return null;
          }
          
          const userData = await userResponse.json();
          
          // Return user with token
          return {
            id: userData.id.toString(),
            email: userData.email,
            name: userData.full_name || userData.email,
            accessToken: tokenData.access_token,
          };
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // First-time jwt callback (after sign-in), add the token
      if (user) {
        token.accessToken = user.accessToken;
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      // Add token and user ID to session
      session.accessToken = token.accessToken;
      session.user.id = token.id;
      return session;
    },
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
  debug: true, // Enable debug mode for troubleshooting
};

export default NextAuth(authOptions);