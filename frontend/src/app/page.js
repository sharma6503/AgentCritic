'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Terminal, Zap } from 'lucide-react';
import Header from '../components/Header';
import InputTabs from '../components/InputTabs';
import ReviewOutput from '../components/ReviewOutput';
import AgentProgress from '../components/AgentProgress';
import AnalysisCard from '../components/AnalysisCard';
import Sidebar from '../components/Sidebar';
import styles from './page.module.css';

const decoder = new TextDecoder();

export default function HomePage() {
    const [sessionsData, setSessionsData] = useState({});

    // ── Sidebar / session state ──────────────────────────────────────────────
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [userId, setUserId] = useState('agent_dev'); // Premium default
    const [activeSessionId, setActiveSessionId] = useState(null);

    const sessionRef = useRef(null);
    const abortControllers = useRef({});

    // Derived active state
    const activeData = activeSessionId && sessionsData[activeSessionId] ? sessionsData[activeSessionId] : {
        output: '',
        progress: '',
        isRunning: false,
        error: '',
        metrics: null,
        agentLogs: [],
        restoredInput: null
    };

    const { output, progress, isRunning, error, metrics, agentLogs, restoredInput } = activeData;

    // Helper to deeply update a specific session's state
    const updateSession = useCallback((sid, updater) => {
        setSessionsData(prev => {
            const current = prev[sid] || { output: '', progress: '', isRunning: false, error: '', metrics: null, agentLogs: [], restoredInput: null };
            return {
                ...prev,
                [sid]: typeof updater === 'function' ? updater(current) : { ...current, ...updater }
            };
        });
    }, []);

    // ── Select an existing session ──────────────────────────
    const handleSelectSession = useCallback(async (sid) => {
        sessionRef.current = sid;
        setActiveSessionId(sid);

        // If we already have data for this session and it's either currently running or already loaded, don't refetch
        if (sessionsData[sid] && (sessionsData[sid].isRunning || sessionsData[sid].output || sessionsData[sid].error)) {
            return;
        }

        updateSession(sid, { progress: 'Retuning session state…', error: '' });

        try {
            const res = await fetch(`/api/sessions/${sid}`);
            if (res.ok) {
                const data = await res.json();

                // Restore metrics if present in metadata
                const fetchedMetrics = data.meta?.metrics || null;

                const messages = data.messages || [];

                // Extract user input
                let fetchedRestoredInput = null;
                const userMsg = messages.find(m => m.role === 'user');
                if (userMsg && userMsg.text) {
                    const text = userMsg.text;
                    if (text.startsWith('Please review this repository: ')) {
                        fetchedRestoredInput = { tab: 'url', url: text.replace('Please review this repository: ', '').trim(), code: '' };
                    } else if (text.startsWith('Please review the following code:')) {
                        const codeMatch = text.match(/```\n([\s\S]*?)\n```/);
                        if (codeMatch) {
                            fetchedRestoredInput = { tab: 'paste', url: '', code: codeMatch[1].trim() };
                        } else {
                            fetchedRestoredInput = { tab: 'paste', url: '', code: text };
                        }
                    } else if (text.includes('uploaded codebase') || text.includes('uploaded file:')) {
                        fetchedRestoredInput = { tab: 'zip', url: '', code: '' };
                    } else {
                        fetchedRestoredInput = { tab: 'paste', url: '', code: text };
                    }
                }

                // Extract agent logs
                const logs = messages.filter(m => m.role === 'model' && m.author && m.author !== 'metrics_agent' && m.author !== 'reviser_agent' && m.author !== 'synthesis_agent');

                // Prioritise the final report from the reviser or synthesiser
                const validTextMsgs = messages.filter(m => m.text && m.text.trim());
                const reportMsg =
                    validTextMsgs.slice().reverse().find(m => m.author === 'reviser_agent') ||
                    validTextMsgs.slice().reverse().find(m => m.author === 'synthesis_agent') ||
                    validTextMsgs.filter(m => m.role === 'model' && m.author !== 'metrics_agent').pop();

                updateSession(sid, {
                    output: reportMsg ? reportMsg.text.trim() : '',
                    metrics: fetchedMetrics,
                    agentLogs: logs,
                    restoredInput: fetchedRestoredInput,
                    progress: ''
                });
            } else {
                updateSession(sid, { error: "Failed to restore session history.", progress: '' });
            }
        } catch (e) {
            console.error("Session restoration failed:", e);
            updateSession(sid, { error: "Failed to restore session history.", progress: '' });
        }
    }, [sessionsData, updateSession]);

    const handleNewSession = useCallback((sid) => {
        sessionRef.current = sid || null;
        setActiveSessionId(sid || null);
        if (sid) {
            updateSession(sid, { output: '', progress: '', isRunning: false, error: '', metrics: null, agentLogs: [], restoredInput: null });
        }
    }, [updateSession]);

    const stopReview = useCallback(() => {
        if (activeSessionId && abortControllers.current[activeSessionId]) {
            abortControllers.current[activeSessionId].abort();
        }
    }, [activeSessionId]);

    const runReview = useCallback(async (fetchFn, sid) => {
        if (!sid) return;

        // Abort previous run for THIS session if any
        if (abortControllers.current[sid]) {
            abortControllers.current[sid].abort();
        }

        const ctrl = new AbortController();
        abortControllers.current[sid] = ctrl;

        updateSession(sid, {
            isRunning: true,
            output: '',
            error: '',
            metrics: null,
            agentLogs: [],
            progress: 'Initializing analysis agents…'
        });

        try {
            const res = await fetchFn(ctrl.signal);
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || 'Analysis service error');
            }

            // In case the backend returns a different ID, though we expect it to respect our passed ID
            const backendSid = res.headers.get('x-session-id');
            const finalSid = backendSid || sid;

            const reader = res.body.getReader();
            let buf = '';
            let full = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buf += decoder.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop() ?? '';

                for (const line of lines) {
                    if (!line.startsWith('data:')) continue;
                    try {
                        const evt = JSON.parse(line.slice(5).trim());
                        if (evt.type === 'progress') {
                            updateSession(finalSid, { progress: evt.message });
                        }
                        if (evt.type === 'delta') {
                            full += evt.text;
                            updateSession(finalSid, { output: full });
                        }
                        if (evt.type === 'metrics') {
                            updateSession(finalSid, { metrics: evt.data });
                        }
                        if (evt.type === 'error') {
                            updateSession(finalSid, { error: evt.message });
                        }
                        if (evt.type === 'agent_log') {
                            updateSession(finalSid, current => {
                                const logs = [...(current.agentLogs || [])];
                                const existingIdx = logs.findIndex(l => l.author === evt.data.author);
                                if (existingIdx > -1) {
                                    logs[existingIdx] = { ...logs[existingIdx], text: evt.data.text };
                                } else {
                                    logs.push(evt.data);
                                }
                                return { agentLogs: logs };
                            });
                        }
                        if (evt.type === 'done') {
                            updateSession(finalSid, { progress: '' });
                        }
                    } catch { }
                }
            }
        } catch (e) {
            if (e.name !== 'AbortError') updateSession(sid, { error: e.message || 'Critical system failure' });
        } finally {
            updateSession(sid, { isRunning: false, progress: '' });
            delete abortControllers.current[sid];
        }
    }, [updateSession]);

    // ── Triggers ──
    const initSessionForTrigger = () => {
        const sid = sessionRef.current || crypto.randomUUID();
        sessionRef.current = sid;
        setActiveSessionId(sid);
        return sid;
    };

    const onUrlReview = (url) => {
        const sid = initSessionForTrigger();
        updateSession(sid, { restoredInput: { tab: 'url', url, code: '' } });
        runReview(sig => fetch('/api/review/url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, session_id: sid, user_id: userId }),
            signal: sig
        }), sid);
    };

    const onZipReview = (file) => {
        const sid = initSessionForTrigger();
        updateSession(sid, { restoredInput: { tab: 'zip', url: '', code: '' } });
        const fd = new FormData();
        fd.append('file', file);
        fd.append('session_id', sid);
        fd.append('user_id', userId);
        runReview(sig => fetch('/api/review/zip', { method: 'POST', body: fd, signal: sig }), sid);
    };

    const onPasteReview = (code) => {
        const sid = initSessionForTrigger();
        updateSession(sid, { restoredInput: { tab: 'paste', url: '', code } });
        runReview(sig => fetch('/api/review/paste', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, session_id: sid, user_id: userId }),
            signal: sig
        }), sid);
    };

    return (
        <div className={`${styles.page} ${sidebarOpen ? styles.pageShifted : ''}`}>
            <Sidebar
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(o => !o)}
                userId={userId}
                onUserChange={setUserId}
                activeSessionId={activeSessionId}
                onSelectSession={handleSelectSession}
                onNewSession={handleNewSession}
            />

            <Header isRunning={isRunning} activeSessionId={activeSessionId} />

            <main className={`${styles.main} animate-in`}>
                <section className={styles.inputSection}>
                    <InputTabs
                        activeSessionId={activeSessionId}
                        isRunning={isRunning}
                        onUrlReview={onUrlReview}
                        onZipReview={onZipReview}
                        onPasteReview={onPasteReview}
                        onStop={stopReview}
                        restoredInput={restoredInput}
                    />
                </section>

                <AnimatePresence mode="wait">
                    {progress && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className={styles.statusWrap}
                        >
                            <AgentProgress label={progress} />
                        </motion.div>
                    )}
                </AnimatePresence>

                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            className={styles.errorBanner}
                        >
                            <AlertCircle size={18} />
                            <span>{error}</span>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className={`${styles.outputGrid} ${metrics ? styles.outputGridHasMetrics : ''}`}>
                    {metrics && (
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={styles.metricsCol}
                        >
                            <AnalysisCard metrics={metrics} />
                        </motion.div>
                    )}

                    <motion.div
                        className={styles.reportCol}
                        layout
                    >
                        <ReviewOutput content={output} isRunning={isRunning} agentLogs={agentLogs} />
                    </motion.div>
                </div>
            </main>

            <footer className={styles.appFooter}>
                <div className={styles.footerInner}>
                    <div className={styles.footerLeft}>
                        <Zap size={14} className={styles.pulseZap} />
                        <span>Powered by ADK Professional Analysis Engine</span>
                    </div>
                    <div className={styles.footerRight}>
                        <span className={styles.statusDot} /> System Operational
                    </div>
                </div>
            </footer>
        </div>
    );
}
