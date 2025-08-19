import { useState, useRef, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import { getSession } from 'next-auth/react';
import toast from 'react-hot-toast';
import Layout from '../components/Layout';
import { queryApi, Source, retrieverApi, conversationApi } from '../utils/api';
import ChatMessage from '../components/ChatMessage';
import SourcesList from '../components/SourcesList';
import AllSourcesModal from '../components/AllSourcesModal';
import ConversationSidebar from '../components/ConversationSidebar';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: Source[];
}

// Sample suggested questions
const suggestedQuestions = [
  "List variants of EoE.",
  "What are the different types of EoE?",
  "Role of IL-13 in the pathogenesis of eosinophilic esophagitis.",
  "What are the FDA-approved treatments for eosinophilic esophagitis?",
  "List statistical methods to study EoE and how they are used?",
  "List statistical analysis tools to study EoE and how they are used?",
  "Explain a statistical treatment plan for EoE after considering the control variables.",
  "Which gene is most correlated with fibrostenosis?",
  "Describe evaluation plan and treatment for refractory EoE."
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [selectedRetriever, setSelectedRetriever] = useState<string>('hybrid');
  const [showAllSources, setShowAllSources] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Update retriever type when selection changes
  useEffect(() => {
    const updateRetrieverType = async () => {
      try {
        await retrieverApi.setRetrieverType(selectedRetriever);
        console.log(`Retriever type set to ${selectedRetriever}`);
      } catch (error) {
        console.error('Error setting retriever type:', error);
        toast.error('Database unavailable—try again later', { 
          duration: 3000,
          style: { background: '#FF5722', color: 'white' }
        });
      }
    };
    
    updateRetrieverType();
  }, [selectedRetriever]);

  // Load conversation when conversation ID changes
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [conversationId]);

  const loadConversation = async (id: number) => {
    try {
      setIsLoading(true);
      const data = await conversationApi.getConversation(id);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Error loading conversation:', error);
      toast.error('Failed to load conversation', {
        duration: 3000,
        style: { background: '#FF5722', color: 'white' }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading) return;
    
    setIsLoading(true);
    
    // Always start a new conversation unless one is explicitly selected by the user
    if (!conversationId) {
      console.log("Starting a new conversation");
    }
    
    // Add user message immediately
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: newMessage,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Send the query to the backend API with selected retriever type
      console.log(`Sending query to backend using ${selectedRetriever} retriever:`, newMessage);
      const result = await queryApi.submitQuery(newMessage, conversationId || undefined, selectedRetriever);
      
      console.log("Received response:", result);
      
      // Set the conversation ID
        setConversationId(result.conversation_id);
      
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
      toast.error('Database unavailable—try again later', { 
        duration: 3000,
        style: { background: '#FF5722', color: 'white' }
      });
      
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
  
  const handleSuggestedQuestion = (question: string) => {
    setNewMessage(question);
  };

  const handleSelectConversation = (id: number) => {
    setConversationId(id);
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
  };

  return (
    <Layout title="Chat | CEGIR">
      {showAllSources && <AllSourcesModal onClose={() => setShowAllSources(false)} />}
      
      <div className="flex h-[calc(100vh-64px)]">
        {/* Conversation sidebar */}
        <ConversationSidebar 
          currentConversationId={conversationId}
          onConversationSelect={handleSelectConversation}
          onNewChat={handleNewChat}
          onSuggestedQuestionClick={handleSuggestedQuestion}
          suggestedQuestions={suggestedQuestions}
        />
        
        <div className="flex flex-col flex-1">
          {/* Retriever type control */}
          <div className="p-3 bg-gray-50 border-b border-gray-200 flex items-center space-x-4">
            <div className="flex-1">
              <div className="flex items-center">
                <label className="text-sm font-medium text-gray-700 mr-2">
                  Retriever Type:
                </label>
                <select
                  value={selectedRetriever}
                  onChange={(e) => setSelectedRetriever(e.target.value)}
                  className="rounded-md border border-gray-300 py-1 px-2 text-sm"
                >
                  <option value="hybrid">Hybrid (Default)</option>
                  <option value="vector_cypher">Vector Cypher</option>
                  <option value="vector">Vector</option>
                </select>
              </div>
            </div>
            
            <button
              onClick={() => setShowAllSources(true)}
              className="text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition-colors"
            >
              View All Sources
            </button>
            
            <button
              onClick={handleNewChat}
              className="text-xs px-2 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            >
              Clear Chat
            </button>
          </div>
          
          {/* Messages container */}
          <div className="flex-1 overflow-y-auto p-4 bg-white">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <h2 className="text-2xl font-bold mb-4">CEGIR Literature Search Assistant</h2>
                  <p className="mb-8">Ask questions about medical research papers and get answers based on the literature.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((msg) => (
                  <div key={msg.id} className="message-container">
                    <ChatMessage message={msg} />
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          
          {/* Suggested questions - moved to sidebar as vertical list */}
          
          {/* Input form */}
          <div className="border-t border-gray-200 p-4 bg-white">
            <form onSubmit={handleSendMessage} className="flex items-end gap-2">
              <div className="flex-1">
                <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (newMessage.trim() && !isLoading) {
                      handleSendMessage(e);
                    }
                  }
                }}
                className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent min-h-[80px] max-h-[160px]"
                placeholder="Ask about eosinophilic disorders... (Press Enter to send, Shift+Enter for new line)"
                disabled={isLoading}
                rows={3}
              />
              </div>
              <button
                type="submit"
                disabled={isLoading || !newMessage.trim()}
                className={`bg-indigo-600 text-white p-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  isLoading || !newMessage.trim() ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <div className="w-6 h-6 border-t-2 border-white rounded-full animate-spin"></div>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                )}
              </button>
            </form>
            </div>
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