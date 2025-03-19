import React from 'react';
import { Message } from '../utils/api';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl rounded-lg px-4 py-2 ${
        isUser 
          ? 'bg-indigo-100 text-indigo-900' 
          : 'bg-white border border-gray-200 text-gray-800'
      }`}>
        <div className="text-sm">
          {message.content.split('\n').map((line, i) => (
            <React.Fragment key={i}>
              {line}
              {i < message.content.split('\n').length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>
        
        {/* Sources list */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <details className="text-xs text-gray-500">
              <summary className="cursor-pointer font-medium">
                Sources ({message.sources.length})
              </summary>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                {message.sources.map((source, index) => (
                  <li key={index} className="truncate">
                    {source.source_name}
                  </li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;