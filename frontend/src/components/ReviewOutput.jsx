'use client';

import { useState } from 'react';
import { Clipboard, ListChecks, Loader2, Search, Terminal } from 'lucide-react';
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
    // Many agents wrap the entire response in a code block
    const fenceRegex = /^```(?:markdown)?\n([\s\S]*?)\n```$/i;
    const match = cleaned.match(fenceRegex);
    if (match) {
        cleaned = match[1].trim();
    }

    // 2. Remove leading/trailing fences if they still exist (sometimes partial or double-wrapped)
    cleaned = cleaned.replace(/^```markdown\n?/i, '');
    cleaned = cleaned.replace(/```$/i, '');

    // 3. Occasionally agents add backticks inside the content that break parsing
    // We only want to strip them if they appear to be wrapping the whole thing.

    return cleaned.trim();
}

export default function ReviewOutput({ content, isRunning, agentLogs = [] }) {
    const [showTraces, setShowTraces] = useState(false);
    const cleanedContent = cleanMarkdown(content);
    const isEmpty = !cleanedContent && agentLogs.length === 0;

    return (
        <div className={`${styles.panel} glass animate-in`}>
            {/* Header bar */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <div className={styles.iconBox}>
                        <ListChecks size={18} />
                    </div>
                    <span className={styles.headerTitle}>Review Analysis</span>
                    {isRunning && !isEmpty && (
                        <div className={styles.streamBadge}>
                            <Loader2 className={styles.spin} size={14} />
                            <span>Synthesizing…</span>
                        </div>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    {agentLogs.length > 0 && (
                        <button
                            className={styles.copyBtn}
                            onClick={() => setShowTraces(s => !s)}
                            title="Toggle intermediate agent traces"
                        >
                            <Terminal size={14} /> <span>{showTraces ? 'Hide Traces' : 'View Traces'}</span>
                        </button>
                    )}
                    {cleanedContent && (
                        <button
                            className={styles.copyBtn}
                            onClick={() => navigator.clipboard?.writeText(cleanedContent)}
                            title="Copy report"
                        >
                            <Clipboard size={14} /> <span>Copy</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Content area */}
            <div className={styles.body}>
                {isEmpty ? (
                    <div className={styles.empty}>
                        {isRunning ? (
                            <div className={styles.waiting}>
                                <Loader2 className={styles.largeSpin} size={40} />
                                <p>Agents are analyzing your code…</p>
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
                    </div>
                ) : showTraces ? (
                    <div style={{ padding: '0 8px' }}>
                        <h3 style={{ marginTop: '0', marginBottom: '16px', fontSize: '18px', color: '#fff' }}>Agent Activity Traces</h3>
                        {agentLogs.map((log, i) => (
                            <div key={i} style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                                <h4 style={{ margin: '0 0 12px 0', textTransform: 'capitalize', fontSize: '14px', color: '#a0a0a0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Terminal size={14} /> {log.author ? log.author.replace(/_/g, ' ') : 'Agent'}
                                </h4>
                                <div className="md">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                                        {cleanMarkdown(log.text)}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <ReviewAccordion content={cleanedContent} />
                )}
            </div>
        </div>
    );
}
