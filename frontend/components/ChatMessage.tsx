import React from 'react';
import { Source } from '../utils/api';
import SourcesList from './SourcesList';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: Source[];
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div 
        className={`rounded-lg p-4 max-w-[80%] ${
        isUser 
            ? 'bg-indigo-50 text-gray-800' 
            : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        {/* Message content */}
        <div className="whitespace-pre-wrap">
          {message.content}
        </div>
        
        {/* Display sources for assistant messages if they exist */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-4">
            <SourcesList sources={message.sources} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;