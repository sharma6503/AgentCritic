import React, { useState } from 'react';
import { MessageSquare, Activity, ChevronRight, ChevronLeft } from 'lucide-react';
import { GlassPanel } from './GlassPanel';
import ReviewOutput from './ReviewOutput';
import AgentProgress from './AgentProgress';

export const RightPanel = ({ reviewData, agentEvents, isReviewing }) => {
    const [activeTab, setActiveTab] = useState('report');
    const [isOpen, setIsOpen] = useState(true);

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed right-4 top-1/2 -translate-y-1/2 p-2 glass border border-white/10 text-white/50 hover:text-white transition-all"
            >
                <ChevronLeft className="w-5 h-5" />
            </button>
        );
    }

    return (
        <div className="w-[450px] flex flex-col h-full pl-4 py-4 pr-4 transition-all duration-500 animate-in">
            <GlassPanel className="flex-1 border-white/10 shadow-void">
                <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/5">
                    <div className="flex gap-4">
                        <button
                            onClick={() => setActiveTab('report')}
                            className={`flex items-center gap-2 py-1 text-xs font-medium border-b-2 transition-all ${activeTab === 'report' ? 'border-blue-500 text-white' : 'border-transparent text-text-muted hover:text-text-secondary'
                                }`}
                        >
                            <MessageSquare className="w-3.5 h-3.5" />
                            REPORT
                        </button>
                        <button
                            onClick={() => setActiveTab('traces')}
                            className={`flex items-center gap-2 py-1 text-xs font-medium border-b-2 transition-all ${activeTab === 'traces' ? 'border-blue-500 text-white' : 'border-transparent text-text-muted hover:text-text-secondary'
                                }`}
                        >
                            <Activity className="w-3.5 h-3.5" />
                            AGENT TRACES
                        </button>
                    </div>
                    <button onClick={() => setIsOpen(false)} className="text-text-muted hover:text-white transition-colors">
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>

                <div className="flex-1 overflow-auto p-4 custom-scrollbar">
                    {activeTab === 'report' ? (
                        <ReviewOutput output={reviewData} />
                    ) : (
                        <AgentProgress events={agentEvents} isComplete={!isReviewing} />
                    )}
                </div>
            </GlassPanel>
        </div>
    );
};
