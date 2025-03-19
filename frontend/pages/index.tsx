import { GetServerSideProps } from 'next';
import { getSession } from 'next-auth/react';
import { useRouter } from 'next/router';
import { useState } from 'react';
import Layout from '../components/Layout';

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleStartChatting = () => {
    setIsLoading(true);
    console.log("Starting chat...");
    // Use direct navigation instead of router.push for more reliability
    window.location.href = '/chat';
  };

  return (
    <Layout title="Home | Medical RAG App">
      <div className="flex flex-col items-center justify-center pt-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          Medical Knowledge Exploration
        </h1>
        <p className="text-xl text-gray-600 mb-8 text-center max-w-2xl">
          Query our medical knowledge graph to get insights from research papers and medical literature.
        </p>
        <button 
          onClick={handleStartChatting}
          disabled={isLoading}
          className={`bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-6 rounded-lg ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
        >
          {isLoading ? 'Loading...' : 'Start Chatting'}
        </button>
      </div>
    </Layout>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const session = await getSession(context);

  if (!session) {
    return {
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }

  return {
    props: { session },
  };
};