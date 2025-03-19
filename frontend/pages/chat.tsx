import { useState } from 'react';
import { GetServerSideProps } from 'next';
import { getSession } from 'next-auth/react';
import toast from 'react-hot-toast';
import Layout from '../components/Layout';
import { queryApi, Source } from '../utils/api';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: Source[];
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading) return;
    
    setIsLoading(true);
    
    // Add user message immediately
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: newMessage,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Send the query to the backend API
      console.log("Sending query to backend:", newMessage);
      const result = await queryApi.submitQuery(newMessage, conversationId || undefined);
      
      console.log("Received response:", result);
      
      // Set the conversation ID if this is a new conversation
      if (!conversationId) {
        setConversationId(result.conversation_id);
      }
      
      // Add the response from the backend
      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.answer,
        created_at: new Date().toISOString(),
        sources: result.sources
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to get response from the RAG system');
      
      // Add error message
      const errorMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again later.',
        created_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout title="Chat | Medical RAG App">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4 h-96 overflow-y-auto border-b">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">
                Send a message to start a conversation with the Medical RAG system
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`p-3 rounded-lg ${
                      msg.role === 'user' 
                        ? 'bg-indigo-100 ml-auto max-w-3/4 text-right' 
                        : 'bg-gray-100 mr-auto max-w-3/4'
                    }`}
                  >
                    <div>{msg.content}</div>
                    
                    {/* Display sources if available */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200 text-left text-xs text-gray-500">
                        <div className="font-semibold">Sources:</div>
                        <ul className="list-disc pl-4">
                          {msg.sources.map((source, idx) => (
                            <li key={idx} className="truncate">{source.source_name}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <form onSubmit={handleSendMessage} className="p-4">
            <div className="flex">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1 border border-gray-300 rounded-l-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Ask about eosinophilic disorders..."
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="bg-indigo-600 text-white px-4 py-2 rounded-r-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
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