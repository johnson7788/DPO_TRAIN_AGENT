import React from 'react';
import { Metadata } from '../types';
import { Info, Tag, Calendar, Database, CheckCircle2 } from 'lucide-react';

interface MetadataPanelProps {
  metadata: Metadata;
}

const MetaItem = ({ icon: Icon, label, value, truncate = false }: any) => (
  <div className="mb-4">
    <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
      <Icon size={12} />
      {label}
    </div>
    <div className={`text-sm text-gray-800 ${truncate ? 'truncate' : 'break-words'}`}>
        {value || <span className="text-gray-400">-</span>}
    </div>
  </div>
);

const MetadataPanel: React.FC<MetadataPanelProps> = ({ metadata }) => {
  return (
    <div className="bg-white border-l border-gray-200 h-full overflow-y-auto w-80 flex-shrink-0 flex flex-col shadow-[0_0_15px_rgba(0,0,0,0.05)] z-10">
      <div className="p-5 border-b border-gray-100 bg-gray-50">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Info size={18} className="text-blue-500" />
            Metadata
        </h2>
        <div className="text-xs text-gray-400 mt-1">ID: {metadata.qid}</div>
      </div>

      <div className="p-5 space-y-2">
        <MetaItem 
            icon={Tag} 
            label="Task Type" 
            value={<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{metadata.task_type}</span>} 
        />

        <MetaItem 
            icon={Calendar} 
            label="Created At" 
            value={metadata.created_at} 
        />
        
        <MetaItem 
            icon={CheckCircle2} 
            label="Chosen Model" 
            value={metadata.chosen_model} 
        />

        <div className="pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                <Database size={12} />
                Ground Truth
            </div>
            <div className="text-sm text-gray-600 bg-amber-50 border border-amber-100 p-3 rounded-md italic">
                {metadata.ground_truth}
            </div>
        </div>

        <div className="pt-4 border-t border-gray-100">
             <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Models Used
            </div>
            <div className="flex flex-wrap gap-2">
                {Object.keys(metadata.models).map(key => (
                    <span key={key} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs border border-gray-200">
                        {key}
                    </span>
                ))}
            </div>
        </div>
      </div>
    </div>
  );
};

export default MetadataPanel;