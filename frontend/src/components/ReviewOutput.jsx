import { useState, useEffect } from 'react';
import { Clipboard, ListChecks, Loader2, Search, Terminal, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReviewAccordion from './ReviewAccordion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import styles from './ReviewOutput.module.css';

/**
 * Robustly strips agent-wrapped markdown fences.
 */
function cleanMarkdown(content) {
    if (!content) return '';
    let cleaned = content.trim();

    // 1. Remove outer ```markdown ... ``` or ``` ... ``` wrappers
    const fenceRegex = /^```(?:markdown)?\n([\s\S]*?)\n```$/i;
    const match = cleaned.match(fenceRegex);
    if (match) {
        cleaned = match[1].trim();
    }

    // 2. Remove leading/trailing fences if they still exist
    cleaned = cleaned.replace(/^```markdown\n?/i, '');
    cleaned = cleaned.replace(/```$/i, '');

    return cleaned.trim();
}

export default function ReviewOutput({ content, isRunning, agentLogs = [] }) {
    const [activeTab, setActiveTab] = useState('report'); // 'report' or 'traces'
    const cleanedContent = cleanMarkdown(content);
    const isEmpty = !cleanedContent && agentLogs.length === 0;

    // Auto-switch to report when content starts arriving
    useEffect(() => {
        if (cleanedContent && activeTab === 'traces' && isRunning) {
            setActiveTab('report');
        }
    }, [cleanedContent, isRunning]);

    // Handle traces tab badge
    const logCount = agentLogs.length;

    return (
        <div className={`${styles.panel} glass animate-in`}>
            {/* Header bar */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <div className={styles.iconBox}>
                        <ListChecks size={18} />
                    </div>
                    <span className={styles.headerTitle}>Review Analysis</span>

                    {/* New Tabbed Navigation */}
                    <div className={styles.tabsContainer}>
                        <button
                            className={`${styles.tab} ${activeTab === 'report' ? styles.tabActive : ''}`}
                            onClick={() => setActiveTab('report')}
                            suppressHydrationWarning
                        >
                            <MessageSquare size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                            Report
                            {activeTab === 'report' && (
                                <motion.div layoutId="tab-indicator" className={styles.tabIndicator} />
                            )}
                        </button>
                        <button
                            className={`${styles.tab} ${activeTab === 'traces' ? styles.tabActive : ''}`}
                            onClick={() => setActiveTab('traces')}
                            suppressHydrationWarning
                        >
                            <Terminal size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                            Agent Traces
                            {logCount > 0 && <span className={styles.tabBadge}>{logCount}</span>}
                            {activeTab === 'traces' && (
                                <motion.div layoutId="tab-indicator" className={styles.tabIndicator} />
                            )}
                        </button>
                    </div>

                    {isRunning && !cleanedContent && (
                        <div className={styles.streamBadge}>
                            <Loader2 className={styles.spin} size={14} />
                            <span>Analyzing…</span>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                    {cleanedContent && (
                        <button
                            className={styles.copyBtn}
                            onClick={() => navigator.clipboard?.writeText(cleanedContent)}
                            title="Copy report"
                            suppressHydrationWarning
                        >
                            <Clipboard size={14} /> <span>Copy</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Content area */}
            <div className={styles.body}>
                <AnimatePresence mode="wait">
                    {isEmpty ? (
                        <motion.div
                            key="empty"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className={styles.empty}
                        >
                            {isRunning ? (
                                <div className={styles.waiting}>
                                    <Loader2 className={styles.largeSpin} size={40} />
                                    <p>Agents are analyzing your code…</p>
                                    <p style={{ fontSize: '0.8rem', opacity: 0.7 }}>Check the Agent Traces tab for real-time activity.</p>
                                </div>
                            ) : (
                                <div className={styles.placeholder}>
                                    <div className={styles.emptyIcon}>
                                        <Search size={48} />
                                    </div>
                                    <h3 className={styles.emptyTitle}>No Analysis Yet</h3>
                                    <p className={styles.emptyHint}>Submit a repository or upload code to start a professional multi-agent review.</p>
                                </div>
                            )}
                        </motion.div>
                    ) : activeTab === 'traces' ? (
                        <motion.div
                            key="traces"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className={styles.traceList}
                        >
                            <h3 style={{ marginTop: '0', marginBottom: '1.5rem', fontSize: '1.1rem', color: '#fff', fontWeight: 600 }}>
                                Live Expert Activity
                            </h3>
                            {agentLogs.length === 0 ? (
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Waiting for expert analysis to start...</p>
                            ) : (
                                agentLogs.map((log, i) => (
                                    <div key={i} className={styles.traceItem}>
                                        <div className={styles.traceItemHeader}>
                                            <Terminal className={styles.traceItemIcon} size={16} />
                                            {log.author ? log.author.replace(/_/g, ' ') : 'Expert Agent'}
                                        </div>
                                        <div className="md">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                                                {cleanMarkdown(log.text)}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                ))
                            )}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="report"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            <ReviewAccordion content={cleanedContent} />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
