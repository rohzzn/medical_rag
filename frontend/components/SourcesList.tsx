import React from 'react';
import { Source } from '../utils/api';

interface SourcesListProps {
  sources: Source[];
}

const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return null;
  }
  
  // Get unique sources
  const uniqueSources = sources.reduce((acc, source) => {
    if (!acc.some(s => s.source_name === source.source_name)) {
      acc.push(source);
    }
    return acc;
  }, [] as Source[]);
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
      <h3 className="font-medium text-gray-800 mb-2">Sources</h3>
      <ul className="divide-y divide-gray-200">
        {uniqueSources.map((source, index) => (
          <li key={index} className="py-2">
            <div className="flex items-start">
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">{source.source_name}</p>
                <p className="text-xs text-gray-500 truncate">{source.source_path}</p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SourcesList;