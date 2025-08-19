import React, { useState } from 'react';
import { Source } from '../utils/api';

interface SourcesListProps {
  sources: Source[];
}

const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  // Always render the sources panel, even if empty
  const uniqueSources = sources && sources.length > 0 
    ? sources.slice(0, 5).reduce((acc, source) => {
        if (!acc.some(s => s.source_name === source.source_name)) {
          acc.push(source);
        }
        return acc;
      }, [] as Source[])
    : [];
  
  const toggleSourceExpand = (sourcePath: string) => {
    if (expandedSource === sourcePath) {
      setExpandedSource(null);
    } else {
      setExpandedSource(sourcePath);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 mb-4">
      <h3 className="font-medium text-gray-800 mb-2">Sources ({uniqueSources.length})</h3>
      {uniqueSources.length === 0 ? (
        <div className="py-3 text-gray-600 text-sm italic">No reliable sources found.</div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {uniqueSources.map((source, index) => (
            <li key={index} className="py-3">
              <div className="flex flex-col">
                <div className="flex items-start mb-1">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="h-5 w-5 text-indigo-500 mr-2 flex-shrink-0 mt-0.5" 
                    viewBox="0 0 20 20" 
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <a 
                      href={source.paper_url || `https://scholar.google.com/scholar?q=${encodeURIComponent(source.source_name)}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:underline"
                    >
                      {source.source_name}
                    </a>
                    <p className="text-xs text-gray-500 truncate max-w-full">{source.paper_id || source.source_path.split('/').pop()}</p>
                  </div>
                  <button
                    onClick={() => toggleSourceExpand(source.source_path)}
                    className="text-gray-400 hover:text-gray-600"
                    aria-label={expandedSource === source.source_path ? "Collapse source" : "Expand source"}
                  >
                    {expandedSource === source.source_path ? (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                </div>
                {expandedSource === source.source_path && (
                  <div className="mt-2 ml-7 text-sm bg-gray-50 p-3 rounded-md border border-gray-100 overflow-auto max-h-64">
                    {source.content && (
                      <div className="mb-2">
                        <h4 className="text-xs text-gray-500 font-medium uppercase mb-1">Exact Passage:</h4>
                        <p className="text-gray-700 whitespace-pre-wrap break-words overflow-wrap-anywhere max-w-full">{source.content}</p>
                      </div>
                    )}
                    {source.location && (
                      <div className="mb-2">
                        <h4 className="text-xs text-gray-500 font-medium uppercase mb-1">Location:</h4>
                        <p className="text-gray-700">{source.location}</p>
                      </div>
                    )}
                    {source.why_it_supports && (
                      <div>
                        <h4 className="text-xs text-gray-500 font-medium uppercase mb-1">Why It Supports:</h4>
                        <p className="text-gray-700">{source.why_it_supports}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SourcesList;