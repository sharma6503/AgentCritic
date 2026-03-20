import React from 'react';
import { Github, Globe, Terminal, Box } from 'lucide-react';

export const RepoHeader = ({ projectName }) => {
    return (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-6 py-3 glass border border-white/10 rounded-full shadow-void animate-in">
            <div className="flex items-center gap-2 pr-4 border-r border-white/10">
                <Box className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-bold tracking-tight text-white whitespace-nowrap">
                    {projectName || 'IM.AGENTIC.REVIEW'}
                </span>
            </div>

            <div className="flex items-center gap-4 pl-2">
                <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full border-2 border-void bg-blue-500/20 flex items-center justify-center">
                        <Github className="w-3 h-3 text-blue-400" />
                    </div>
                    <div className="w-6 h-6 rounded-full border-2 border-void bg-cyan-500/20 flex items-center justify-center">
                        <Terminal className="w-3 h-3 text-cyan-400" />
                    </div>
                </div>
                <div className="flex flex-col">
                    <span className="text-[10px] font-bold text-text-muted uppercase leading-tight">Status</span>
                    <span className="text-[10px] font-bold text-blue-400 uppercase leading-tight">Analyzing...</span>
                </div>
            </div>
        </div>
    );
};
