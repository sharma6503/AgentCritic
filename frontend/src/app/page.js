"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import {
    Github,
    Upload,
    Type,
    Play,
    ShieldCheck,
    Terminal,
    Settings as SettingsIcon,
    Search,
    Menu,
    X,
    FolderTree,
    MessageSquare,
    Activity,
    Layers,
    ChevronRight,
    Zap
} from 'lucide-react';
import { GlassPanel } from '../components/GlassPanel';
import { Sidebar } from '../components/Sidebar';
import { RightPanel } from '../components/RightPanel';
import { RepoHeader } from '../components/RepoHeader';

// Dynamic import for GraphCanvas to avoid SSR issues with Sigma.js
const GraphCanvas = dynamic(() => import('../components/GraphCanvas').then(mod => mod.GraphCanvas), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center bg-void text-blue-500/50">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
                <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Initializing Canvas...</span>
            </div>
        </div>
    )
});

export default function HomePage() {
    // UI State
    const [activeTab, setActiveTab] = useState('github');
    const [projectName, setProjectName] = useState('');
    const [isSidebarOpen, setSidebarOpen] = useState(true);
    const [isRightPanelOpen, setRightPanelOpen] = useState(true);
    const [fileTree, setFileTree] = useState([]);

    // Logic State
    const [githubUrl, setGithubUrl] = useState('');
    const [pasteCode, setPasteCode] = useState('');
    const [isReviewing, setIsReviewing] = useState(false);
    const [events, setEvents] = useState([]);
    const [reviewOutput, setReviewOutput] = useState('');
    const [graphData, setGraphData] = useState(null);

    // Refs
    const eventSourceRef = useRef(null);

    // Build file tree from flat paths if needed
    const buildFileTree = (files) => {
        const root = [];
        files.forEach(path => {
            const parts = path.split('/');
            let currentLevel = root;
            parts.forEach((part, i) => {
                let existingPath = currentLevel.find(p => p.name === part);
                if (!existingPath) {
                    existingPath = {
                        name: part,
                        path: parts.slice(0, i + 1).join('/'),
                        type: i === parts.length - 1 ? 'file' : 'directory',
                        children: []
                    };
                    currentLevel.push(existingPath);
                }
                currentLevel = existingPath.children;
            });
        });
        return root;
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setProjectName(file.name.replace('.zip', ''));
        setEvents([]);
        setReviewOutput('');
        setIsReviewing(true);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:8007/api/review/zip", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Upload failed");
            setupEventSource(response.headers.get("X-Session-Id"));
        } catch (error) {
            setEvents(prev => [...prev, { type: 'error', message: error.message }]);
            setIsReviewing(false);
        }
    };

    const handleGithubReview = async () => {
        if (!githubUrl) return;

        setEvents([]);
        setReviewOutput('');
        setIsReviewing(true);
        setProjectName(githubUrl.split('/').pop() || 'Repository');

        try {
            const response = await fetch("http://localhost:8007/api/review/url", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: githubUrl }),
            });

            if (!response.ok) throw new Error("Request failed");
            setupEventSource(response.headers.get("X-Session-Id"));
        } catch (error) {
            setEvents(prev => [...prev, { type: 'error', message: error.message }]);
            setIsReviewing(false);
        }
    };

    const setupEventSource = (sessionId) => {
        if (eventSourceRef.current) eventSourceRef.current.close();

        const url = `http://localhost:8007/api/review/stream?session_id=${sessionId}`;
        const es = new EventSource(url);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'delta') {
                setReviewOutput(prev => prev + data.content);
            } else if (data.type === 'graph_data') {
                setGraphData(data.data);
                // Extract file list for tree
                if (data.data.nodes) {
                    const filePaths = data.data.nodes
                        .filter(n => n.metadata?.type === 'file' || n.id.includes('.'))
                        .map(n => n.id);
                    setFileTree(buildFileTree(filePaths));
                }
            } else if (data.type === 'progress' || data.type === 'metrics' || data.type === 'error') {
                setEvents(prev => [...prev, data]);
            } else if (data.type === 'done') {
                setIsReviewing(false);
                es.close();
            }
        };

        es.onerror = (err) => {
            console.error("SSE Error:", err);
            setIsReviewing(false);
            es.close();
        };
    };

    return (
        <main className="relative h-screen w-screen bg-void overflow-hidden flex flex-col font-sans">
            {/* Background Canvas (Fixed to viewport to ensure height) */}
            <div className="fixed inset-0 z-0 overflow-hidden">
                <GraphCanvas graphData={graphData} />
            </div>

            {/* Overlays */}
            <RepoHeader projectName={projectName} />

            {/* Floating Sidebar Toggle (When closed) */}
            {!isSidebarOpen && (
                <button
                    onClick={() => setSidebarOpen(true)}
                    className="fixed left-4 top-4 z-50 p-2 glass border border-white/10 text-white shadow-void"
                >
                    <Menu className="w-5 h-5" />
                </button>
            )}

            {/* Layout Wrapper */}
            <div className="relative z-10 flex-1 flex h-full overflow-hidden">
                {/* Fixed Height Sidebars */}
                <div className={`h-full transition-all duration-500 overflow-hidden ${isSidebarOpen ? 'w-72 opacity-100' : 'w-0 opacity-0'}`}>
                    <Sidebar
                        fileTreeData={fileTree}
                        onFileSelect={(path) => console.log('Selected:', path)}
                        onOpenSettings={() => console.log('Open Settings')}
                    />
                </div>

                <div className="flex-1 flex flex-col items-center justify-center pointer-events-none">
                    {/* Centered Input Panel (Visible when no project loaded) */}
                    {!graphData && !isReviewing && (
                        <div className="w-full max-w-xl animate-in pointer-events-auto px-4">
                            <GlassPanel className="p-8 border-white/5 bg-void/40">
                                <div className="flex flex-col items-center text-center mb-10">
                                    <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20">
                                        <Layers className="w-8 h-8 text-blue-400" />
                                    </div>
                                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Connect Your Workspace</h1>
                                    <p className="text-sm text-text-muted">Enter a repository URL or upload a local archive to begin structural analysis.</p>
                                </div>

                                <div className="flex bg-white/5 p-1 rounded-lg mb-6 border border-white/5">
                                    <button
                                        onClick={() => setActiveTab('github')}
                                        className={`flex-1 py-2 text-xs font-bold transition-all rounded-md ${activeTab === 'github' ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-text-muted hover:text-text-secondary'}`}
                                    >
                                        GITHUB
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('upload')}
                                        className={`flex-1 py-2 text-xs font-bold transition-all rounded-md ${activeTab === 'upload' ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-text-muted hover:text-text-secondary'}`}
                                    >
                                        ARCHIVE
                                    </button>
                                </div>

                                {activeTab === 'github' ? (
                                    <div className="space-y-4">
                                        <div className="relative">
                                            <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                                            <input
                                                type="text"
                                                placeholder="https://github.com/organization/repo"
                                                className="w-full bg-void/50 border border-white/10 rounded-lg py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all font-mono"
                                                value={githubUrl}
                                                onChange={(e) => setGithubUrl(e.target.value)}
                                            />
                                        </div>
                                        <button
                                            onClick={handleGithubReview}
                                            disabled={!githubUrl || isReviewing}
                                            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold py-3 rounded-lg shadow-lg shadow-blue-600/20 transition-all flex items-center justify-center gap-2"
                                        >
                                            <Play className="w-4 h-4 fill-current" />
                                            START ANALYSIS
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-xl bg-void/50 cursor-pointer hover:bg-white/5 hover:border-blue-500/30 transition-all group">
                                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                                <Upload className="w-8 h-8 text-text-muted mb-2 group-hover:text-blue-400 transition-colors" />
                                                <p className="text-xs text-text-muted group-hover:text-text-secondary">Drop .zip or Click to browse</p>
                                            </div>
                                            <input type="file" className="hidden" accept=".zip" onChange={handleFileUpload} />
                                        </label>
                                    </div>
                                )}
                            </GlassPanel>
                        </div>
                    )}
                </div>

                {/* Right Panel Output Overaly */}
                {(isReviewing || graphData) && (
                    <div className="h-full flex-shrink-0">
                        <RightPanel
                            reviewData={reviewOutput}
                            agentEvents={events}
                            isReviewing={isReviewing}
                        />
                    </div>
                )}
            </div>

            {/* Bottom Status Bar */}
            <div className="relative z-50 h-8 bg-void/80 backdrop-blur-md border-t border-white/5 px-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Engine Ready</span>
                    </div>
                    {isReviewing && (
                        <div className="flex items-center gap-2 text-blue-400 animate-pulse">
                            <Activity className="w-3 h-3" />
                            <span className="text-[10px] font-bold uppercase tracking-wider">Processing Stream...</span>
                        </div>
                    )}
                </div>
                <div className="text-[10px] font-medium text-text-muted">
                    v0.2.0-beta • ADK Framework • GitNexus Core
                </div>
            </div>
        </main>
    );
}

