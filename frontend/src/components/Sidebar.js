import React from 'react';
import { GlassPanel } from './GlassPanel';
import { FileTree } from './FileTree';
import { FolderTree, Settings, Github, Cpu } from 'lucide-react';

export const Sidebar = ({ fileTreeData, onFileSelect, onOpenSettings }) => {
    return (
        <div className="w-72 flex flex-col h-full py-4 pl-4 animate-in">
            <GlassPanel title="WORKSPACE" icon={FolderTree} className="flex-1">
                <div className="p-2 h-full overflow-auto custom-scrollbar">
                    <FileTree data={fileTreeData} onSelect={onFileSelect} />
                </div>
            </GlassPanel>

            <div className="mt-4 flex flex-col gap-2">
                <button
                    onClick={onOpenSettings}
                    className="flex items-center gap-3 px-4 py-3 glass border border-white/5 hover:bg-white/10 text-text-secondary hover:text-white transition-all rounded-xl"
                >
                    <Settings className="w-4 h-4" />
                    <span className="text-xs font-semibold tracking-wide uppercase">Settings</span>
                </button>

                <div className="px-4 py-3 glass border border-white/5 bg-blue-500/10 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">System Online</span>
                    </div>
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                </div>
            </div>
        </div>
    );
};
