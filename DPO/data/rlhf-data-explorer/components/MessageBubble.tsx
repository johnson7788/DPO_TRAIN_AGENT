import React from 'react';
import { Message } from '../types';
import { User, Bot, Terminal, Server, Database } from 'lucide-react';
import JsonViewer from './JsonViewer';

interface MessageBubbleProps {
  message: Message;
}

const RoleIcon = ({ role }: { role: Message['role'] }) => {
  switch (role) {
    case 'user': return <User size={16} className="text-white" />;
    case 'assistant': return <Bot size={16} className="text-blue-600" />;
    case 'system': return <Server size={16} className="text-purple-600" />;
    case 'tool_call': return <Terminal size={16} className="text-amber-600" />;
    case 'tool_response': return <Database size={16} className="text-emerald-600" />;
    default: return <Bot size={16} />;
  }
};

const RoleLabel = ({ role }: { role: Message['role'] }) => {
    switch (role) {
      case 'user': return 'User';
      case 'assistant': return 'Assistant';
      case 'system': return 'System Prompt';
      case 'tool_call': return 'Tool Call';
      case 'tool_response': return 'Tool Response';
      default: return role;
    }
  };

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isTool = message.role === 'tool_call' || message.role === 'tool_response' || message.role === 'system';
  
  // Parse tool content if possible to see if it has SQL
  let sqlSnippet = null;
  if (message.role === 'tool_call') {
      try {
          const parsed = JSON.parse(message.content);
          if (parsed.arguments?.sql) {
              sqlSnippet = parsed.arguments.sql;
          }
      } catch (e) {}
  }

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[90%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
        
        {/* Avatar */}
        <div className={`
            flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 shadow-sm
            ${isUser ? 'bg-blue-600' : 'bg-white border border-gray-200'}
        `}>
          <RoleIcon role={message.role} />
        </div>

        {/* Content Body */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} min-w-0 flex-1`}>
            <span className="text-xs text-gray-400 mb-1 ml-1 capitalize flex items-center gap-1">
                <RoleLabel role={message.role} />
            </span>

            <div className={`
                relative px-4 py-3 rounded-2xl text-sm leading-6 shadow-sm overflow-hidden w-full
                ${isUser ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'}
                ${isTool ? 'bg-slate-50 font-mono text-xs border-dashed border-gray-300' : ''}
            `}>
                
                {/* Specific Handling for Tool Calls with SQL */}
                {sqlSnippet && (
                     <div className="mb-2 p-2 bg-slate-800 rounded text-green-400 border border-slate-700 overflow-x-auto">
                        <div className="text-[10px] text-slate-400 uppercase tracking-widest mb-1">SQL Query</div>
                        <code>{sqlSnippet}</code>
                     </div>
                )}

                {/* Main Content Rendering */}
                {isTool ? (
                    <JsonViewer 
                        data={message.content} 
                        initialExpanded={message.role !== 'tool_response'} // Auto-collapse massive responses
                        className={message.role === 'tool_response' ? 'border-emerald-200 bg-emerald-50/30' : ''}
                        label={message.role === 'tool_response' ? 'View Tool Output' : 'View Tool Arguments'}
                    />
                ) : (
                    <div className="whitespace-pre-wrap break-words">
                        {message.content}
                    </div>
                )}
            </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;