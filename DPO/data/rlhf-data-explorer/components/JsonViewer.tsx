import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';

interface JsonViewerProps {
  data: string | object;
  initialExpanded?: boolean;
  className?: string;
  label?: string;
}

const JsonViewer: React.FC<JsonViewerProps> = ({ data, initialExpanded = false, className = "", label }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [copied, setCopied] = useState(false);

  let parsedData: any = data;
  let isJsonString = false;

  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data);
      isJsonString = true;
    } catch (e) {
      // Not JSON, just display string
      parsedData = data;
    }
  }

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const textToCopy = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isObject = parsedData !== null && typeof parsedData === 'object';
  const isEmpty = isObject && Object.keys(parsedData).length === 0;

  if (!isObject && !isJsonString) {
      return <div className={`font-mono text-sm whitespace-pre-wrap ${className}`}>{String(parsedData)}</div>;
  }

  return (
    <div className={`border border-gray-200 rounded-md overflow-hidden bg-slate-50 ${className}`}>
      <div 
        className="flex items-center justify-between px-3 py-2 bg-gray-100 cursor-pointer select-none hover:bg-gray-200 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wider">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {label || (Array.isArray(parsedData) ? `Array [${parsedData.length}]` : 'JSON Object')}
        </div>
        <button 
            onClick={handleCopy}
            className="p-1 hover:bg-gray-300 rounded text-gray-500 hover:text-gray-700 transition-colors"
            title="Copy Raw JSON"
        >
            {copied ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
        </button>
      </div>
      
      {isExpanded && (
        <div className="p-3 overflow-x-auto bg-white">
          {isEmpty ? (
            <span className="text-gray-400 italic text-sm">Empty</span>
          ) : (
             <pre className="text-xs font-mono text-slate-700 leading-relaxed">
                {JSON.stringify(parsedData, null, 2)}
             </pre>
          )}
        </div>
      )}
    </div>
  );
};

export default JsonViewer;