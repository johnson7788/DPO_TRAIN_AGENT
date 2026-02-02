import React, { useEffect, useState } from 'react';
import { DataItem, Message } from './types';
import { fetchDataByIndex, fetchTotalCount } from './services/api';
import MessageBubble from './components/MessageBubble';
import MetadataPanel from './components/MetadataPanel';
import { ChevronLeft, ChevronRight, RefreshCw, Layers, XCircle, CheckCircle2 } from 'lucide-react';

const App: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DataItem | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [viewMode, setViewMode] = useState<'chosen' | 'rejected'>('chosen');

  useEffect(() => {
    const init = async () => {
      const total = await fetchTotalCount();
      setTotalCount(total);
      loadData(0);
    };
    init();
  }, []);

  const loadData = async (index: number) => {
    setLoading(true);
    try {
      const item = await fetchDataByIndex(index);
      setData(item);
      setCurrentIndex(index);
      setViewMode('chosen'); // Reset view mode on new data
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (currentIndex < totalCount - 1) loadData(currentIndex + 1);
  };

  const handlePrev = () => {
    if (currentIndex > 0) loadData(currentIndex - 1);
  };

  const activeMessages = viewMode === 'chosen' ? data?.messages : data?.rejected_messages;

  return (
    <div className="flex flex-col h-screen bg-gray-100 text-gray-900 font-sans">
      
      {/* Header / Navigation Bar */}
      <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6 shadow-sm z-20">
        <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-1.5 rounded-lg">
                <Layers className="text-white" size={20} />
            </div>
            <div>
                <h1 className="font-bold text-gray-800 text-lg leading-tight">Dataset Explorer</h1>
                <p className="text-xs text-gray-500">Medical RLHF Workbench</p>
            </div>
        </div>

        <div className="flex items-center gap-4 bg-gray-50 p-1 rounded-lg border border-gray-200">
            <button 
                onClick={handlePrev} 
                disabled={currentIndex === 0 || loading}
                className="p-2 rounded hover:bg-white hover:shadow-sm disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:shadow-none transition-all"
            >
                <ChevronLeft size={18} />
            </button>
            <span className="text-sm font-medium w-24 text-center">
                {loading ? '...' : `${currentIndex + 1} / ${totalCount}`}
            </span>
            <button 
                onClick={handleNext} 
                disabled={currentIndex === totalCount - 1 || loading}
                className="p-2 rounded hover:bg-white hover:shadow-sm disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:shadow-none transition-all"
            >
                <ChevronRight size={18} />
            </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Center: Conversation View */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
            
            {/* View Toggle (Chosen vs Rejected) */}
            {data?.rejected_messages && (
                <div className="absolute top-4 left-0 right-0 z-10 flex justify-center">
                    <div className="bg-white/90 backdrop-blur-sm shadow-md rounded-full p-1 flex border border-gray-200">
                        <button
                            onClick={() => setViewMode('chosen')}
                            className={`px-4 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 transition-colors ${
                                viewMode === 'chosen' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
                            }`}
                        >
                            <CheckCircle2 size={14} />
                            Chosen Response
                        </button>
                        <button
                            onClick={() => setViewMode('rejected')}
                            className={`px-4 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 transition-colors ${
                                viewMode === 'rejected' ? 'bg-red-50 text-red-700 ring-1 ring-red-200' : 'text-gray-600 hover:bg-gray-100'
                            }`}
                        >
                            <XCircle size={14} />
                            Rejected Response
                        </button>
                    </div>
                </div>
            )}

            {loading ? (
                <div className="flex-1 flex items-center justify-center text-gray-400 gap-2">
                    <RefreshCw className="animate-spin" /> Loading data...
                </div>
            ) : data && activeMessages ? (
                <div className="flex-1 overflow-y-auto px-4 py-8 md:px-16 scroll-smooth">
                    <div className="max-w-3xl mx-auto pb-20 pt-8">
                        {activeMessages.map((msg: Message, idx: number) => (
                            <MessageBubble key={idx} message={msg} />
                        ))}
                        
                        <div className="flex justify-center mt-12 mb-8">
                            <div className="h-px bg-gray-200 w-full max-w-xs relative">
                                <span className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-100 px-3 text-xs text-gray-400">
                                    End of Conversation
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="flex-1 flex items-center justify-center text-gray-400">
                    No data available
                </div>
            )}
        </main>

        {/* Right Sidebar: Metadata */}
        {data && !loading && (
             <MetadataPanel metadata={data.metadata} />
        )}
      </div>
    </div>
  );
};

export default App;