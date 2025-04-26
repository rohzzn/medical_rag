import React, { useState, useEffect } from 'react';
import { conversationApi, Conversation } from '../utils/api';

interface ConversationSidebarProps {
  currentConversationId: number | null;
  onConversationSelect: (id: number) => void;
  onNewChat: () => void;
}

const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  currentConversationId,
  onConversationSelect,
  onNewChat
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Function to fetch conversations
  const fetchConversations = async () => {
    try {
      setIsLoading(true);
      const data = await conversationApi.getAllConversations();
      console.log("Fetched conversations:", data);
      setConversations(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch conversations on component mount and when currentConversationId changes
  useEffect(() => {
    fetchConversations();
    
    // Refresh the conversation list every 10 seconds to get latest changes
    const intervalId = setInterval(() => {
      fetchConversations();
    }, 10000);
    
    return () => clearInterval(intervalId);
  }, [currentConversationId]);

  // Format date to a readable format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMinutes = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    
    if (diffInMinutes < 1) {
      return 'just now';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes} min${diffInMinutes === 1 ? '' : 's'} ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
    } else if (diffInDays < 7) {
      return `${diffInDays} day${diffInDays === 1 ? '' : 's'} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  // Truncate title to a max length
  const truncateTitle = (title: string, maxLength: number = 30) => {
    if (!title) return "Untitled conversation";
    if (title.length <= maxLength) return title;
    return title.substring(0, maxLength) + '...';
  };

  return (
    <>
      {/* Mobile toggle button */}
      <button
        className="md:hidden fixed top-16 left-4 z-20 p-2 bg-indigo-600 text-white rounded-md"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? 'Close' : 'Menu'}
      </button>

      {/* Sidebar container */}
      <div 
        className={`bg-gray-50 border-r border-gray-200 w-64 flex-shrink-0 flex flex-col 
          transition-all duration-300 ease-in-out
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
          md:translate-x-0 fixed md:static h-[calc(100vh-64px)] z-10`}
      >
        {/* New chat button */}
        <div className="p-4">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 mr-2"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                clipRule="evenodd"
              />
            </svg>
            New Chat
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-4 py-2">
            Conversations ({conversations.length})
          </h2>
          
          {isLoading && conversations.length === 0 ? (
            <div className="flex justify-center p-4">
              <div className="w-5 h-5 border-t-2 border-indigo-500 rounded-full animate-spin"></div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500">
              No conversations yet. Start a new chat to begin!
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {conversations.map((conversation) => (
                <li key={conversation.id}>
                  <button
                    onClick={() => onConversationSelect(conversation.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-100 focus:outline-none ${
                      currentConversationId === conversation.id
                        ? 'bg-indigo-50 border-l-4 border-indigo-500'
                        : ''
                    }`}
                  >
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {truncateTitle(conversation.title)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(conversation.updated_at)}
                        {' • '}
                        {conversation.messages.length} message{conversation.messages.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
};

export default ConversationSidebar; 