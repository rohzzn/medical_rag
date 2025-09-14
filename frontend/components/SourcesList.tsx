import React, { useState } from 'react';
import { Source } from '../utils/api';

interface SourcesListProps {
  sources: Source[];
}

const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  // Debug logging
  console.log("SourcesList received sources:", sources);
  console.log("Sources type:", typeof sources);
  console.log("Sources length:", sources?.length || 0);
  if (sources && sources.length > 0) {
    console.log("First source structure:", sources[0]);
  }

  // Always render the sources panel, even if empty
  const uniqueSources = sources && sources.length > 0 
    ? sources.slice(0, 5).reduce((acc, source) => {
        if (!acc.some(s => s.source_name === source.source_name)) {
          acc.push(source);
        }
        return acc;
      }, [] as Source[])
    : [];
  
  console.log("Unique sources after processing:", uniqueSources.length);
  
  const toggleSourceExpand = (sourcePath: string) => {
    if (expandedSource === sourcePath) {
      setExpandedSource(null);
    } else {
      setExpandedSource(sourcePath);
    }
  };
  
  return (
    <>
      <style jsx>{`
        .source-content {
          word-break: break-word !important;
          overflow-wrap: anywhere !important;
          hyphens: auto !important;
          max-width: 100% !important;
          overflow: hidden !important;
        }
        .source-container {
          min-width: 0 !important;
          width: 100% !important;
          overflow: hidden !important;
        }
        .source-item-clickable {
          transition: background-color 0.2s ease;
        }
        .source-item-clickable:hover {
          background-color: #f9fafb;
        }
      `}</style>
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 mb-4 source-container">
        <h3 className="font-medium text-gray-800 mb-2">Sources ({uniqueSources.length})</h3>
      {uniqueSources.length === 0 ? (
        <div className="py-3 text-gray-600 text-sm italic">
          {sources && sources.length > 0 ? "Processing sources..." : "No sources found for this query."}
        </div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {uniqueSources.map((source, index) => (
            <li key={index} className="py-3">
              <div className="flex flex-col">
                <div 
                  className="flex items-start mb-1 cursor-pointer rounded p-1 -m-1 source-item-clickable"
                  onClick={() => toggleSourceExpand(source.source_path)}
                >
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="h-5 w-5 text-indigo-500 mr-2 flex-shrink-0 mt-0.5" 
                    viewBox="0 0 20 20" 
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <a 
                      href={source.paper_url || `https://scholar.google.com/scholar?q=${encodeURIComponent(source.source_name)}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:underline block break-words hyphens-auto leading-tight"
                      style={{
                        wordBreak: 'break-word',
                        overflowWrap: 'anywhere',
                        hyphens: 'auto'
                      }}
                    >
                      {source.source_name}
                    </a>
                    <p className="text-xs text-gray-500 break-words mt-1 leading-tight" style={{wordBreak: 'break-word'}}>
                      {source.paper_id || source.source_path.split('/').pop()}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSourceExpand(source.source_path);
                    }}
                    className="text-gray-400 hover:text-gray-600 flex-shrink-0 p-1"
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
                  <div className="mt-2 ml-7 text-sm bg-gray-50 p-3 rounded-md border border-gray-100 max-h-64 overflow-hidden">
                    {source.content && (
                      <div className="mb-2 min-w-0 w-full">
                        <h4 className="text-xs text-gray-500 font-medium uppercase mb-1">Content:</h4>
                        <div className="text-gray-700 text-sm leading-relaxed overflow-hidden min-w-0 w-full source-content">
                          {source.content}
                        </div>
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
    </>
  );
};

export default SourcesList;