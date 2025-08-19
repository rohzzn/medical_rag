import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useSession, signOut } from 'next-auth/react';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title = 'CEGIR Literature Search Assistant' }) => {
  const { data: session, status } = useSession();
  const router = useRouter();
  const isLoading = status === 'loading';
  
  // Handle logout
  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push('/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>{title}</title>
        <meta name="description" content="CEGIR Literature Search Assistant" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link href="/" className="text-xl font-bold text-indigo-600 truncate max-w-xs">
                  CEGIR 
                </Link>
              </div>
              {session && (
                <nav className="ml-6 flex space-x-8">
                  <Link 
                    href="/chat" 
                    className={`inline-flex items-center px-1 pt-1 border-b-2 ${
                      router.pathname === '/chat' 
                        ? 'border-indigo-500 text-gray-900' 
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    Chat
                  </Link>
                </nav>
              )}
            </div>
            
            <div className="flex items-center">
              {isLoading ? (
                <div className="h-8 w-8 rounded-full bg-gray-200 animate-pulse"></div>
              ) : session ? (
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-700">
                    {session.user?.name || session.user?.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex space-x-4">
                  <Link
                    href="/login"
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    Login
                  </Link>
                  <Link
                    href="/register"
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      
      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
    </div>
  );
};

export default Layout;