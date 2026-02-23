'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Plus, History, Edit2, Trash2, ArrowRight, X, LayoutGrid } from 'lucide-react';
import styles from './Sidebar.module.css';

// Relative time formatter
function timeAgo(isoStr) {
    if (!isoStr) return '';
    const diff = (Date.now() - new Date(isoStr).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

export default function Sidebar({
    isOpen, onToggle,
    userId, onUserChange,
    activeSessionId, onSelectSession, onNewSession,
}) {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [userInput, setUserInput] = useState(userId || 'default');
    const [editId, setEditId] = useState(null);
    const [editName, setEditName] = useState('');
    const [mounted, setMounted] = useState(false);
    const editRef = useRef(null);

    useEffect(() => { setMounted(true); }, []);

    const refresh = useCallback(async (uid) => {
        if (!uid) return;
        setLoading(true);
        try {
            const res = await fetch(`/api/users/${encodeURIComponent(uid)}/sessions`);
            if (res.ok) {
                const data = await res.json();
                setSessions(data.sessions || []);
            }
        } catch { }
        setLoading(false);
    }, []);

    useEffect(() => { if (isOpen) refresh(userId); }, [isOpen, userId, refresh]);

    useEffect(() => {
        if (editId) editRef.current?.focus();
    }, [editId]);

    const applyUserSwitch = () => {
        const uid = userInput.trim() || 'default';
        onUserChange(uid);
        refresh(uid);
    };

    const handleNew = async () => {
        try {
            const res = await fetch(`/api/users/${encodeURIComponent(userId)}/sessions`, { method: 'POST' });
            if (res.ok) {
                const session = await res.json();
                setSessions(s => [session, ...s]);
                onNewSession(session.id);
            }
        } catch { }
    };

    const handleDelete = async (e, sid) => {
        e.stopPropagation();
        try {
            await fetch(`/api/sessions/${sid}`, { method: 'DELETE' });
            setSessions(s => s.filter(x => x.id !== sid));
            if (activeSessionId === sid) onNewSession(null);
        } catch { }
    };

    const startRename = (e, session) => {
        e.stopPropagation();
        setEditId(session.id);
        setEditName(session.name);
    };

    const commitRename = async (sid) => {
        if (!editName.trim()) { setEditId(null); return; }
        try {
            const res = await fetch(`/api/sessions/${sid}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: editName.trim() }),
            });
            if (res.ok) {
                const updated = await res.json();
                setSessions(s => s.map(x => x.id === sid ? { ...x, name: updated.name } : x));
            }
        } catch { }
        setEditId(null);
    };

    return (
        <>
            <button
                className={`${styles.toggle} ${isOpen ? styles.toggleOpen : ''} glass`}
                onClick={onToggle}
                title={isOpen ? 'Collapse' : 'Expand'}
                suppressHydrationWarning
            >
                {isOpen ? <X size={20} /> : <LayoutGrid size={20} />}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.aside
                        className={`${styles.panel} glass`}
                        initial={{ x: -280 }}
                        animate={{ x: 0 }}
                        exit={{ x: -280 }}
                        transition={{ type: 'spring', damping: 20, stiffness: 100 }}
                    >
                        {/* Header */}
                        <div className={styles.panelHeader}>
                            <div className={styles.logoCircle}>
                                <History size={20} />
                            </div>
                            <span className={styles.panelTitle}>Management</span>
                        </div>

                        {/* User switcher */}
                        <div className={styles.userBox}>
                            <div className={styles.userLabel}>
                                <User size={14} /> <span>CURRENT USER</span>
                            </div>
                            <div className={styles.userRow}>
                                <input
                                    className={styles.userInput}
                                    value={userInput}
                                    onChange={e => setUserInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && applyUserSwitch()}
                                    placeholder="user id…"
                                    suppressHydrationWarning
                                />
                                <button className={styles.switchBtn} onClick={applyUserSwitch} suppressHydrationWarning>
                                    <ArrowRight size={16} />
                                </button>
                            </div>
                        </div>

                        {/* New session button */}
                        <button className={styles.newBtn} onClick={handleNew} suppressHydrationWarning>
                            <Plus size={18} /> <span>New Session</span>
                        </button>

                        {/* Session list */}
                        <div className={styles.listLabel}>
                            <History size={14} /> <span>RECENT REVIEWS</span>
                            {loading && <Loader2 className={styles.listLoader} size={14} />}
                        </div>

                        <div className={styles.list}>
                            {sessions.length === 0 && !loading && (
                                <div className={styles.empty}>No activity found.</div>
                            )}
                            {sessions.map(s => (
                                <div
                                    key={s.id}
                                    className={`${styles.item} ${s.id === activeSessionId ? styles.itemActive : ''}`}
                                    onClick={() => onSelectSession(s.id)}
                                >
                                    {editId === s.id ? (
                                        <input
                                            ref={editRef}
                                            className={styles.renameInput}
                                            value={editName}
                                            onChange={e => setEditName(e.target.value)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') commitRename(s.id);
                                                if (e.key === 'Escape') setEditId(null);
                                            }}
                                            onBlur={() => commitRename(s.id)}
                                            onClick={e => e.stopPropagation()}
                                            suppressHydrationWarning
                                        />
                                    ) : (
                                        <>
                                            <div className={styles.itemMain}>
                                                <div className={styles.itemName}>
                                                    {s.name} <span style={{ fontSize: '10px', opacity: 0.6, marginLeft: '6px', fontWeight: 'normal' }} title={s.id}>({s.id})</span>
                                                </div>
                                                <div className={styles.itemPreview}>{s.preview}</div>
                                            </div>
                                            <div className={styles.itemFooter}>
                                                <span className={styles.itemTime}>{mounted ? timeAgo(s.updated_at) : ''}</span>
                                                <div className={styles.itemActions}>
                                                    <button onClick={e => startRename(e, s)} suppressHydrationWarning><Edit2 size={12} /></button>
                                                    <button onClick={e => handleDelete(e, s.id)} className={styles.del} suppressHydrationWarning><Trash2 size={12} /></button>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            ))}
                        </div>

                        <div className={styles.footer}>
                            <span>v1.5 Premium Edition</span>
                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>
        </>
    );
}

const Loader2 = ({ className, size }) => (
    <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
        className={className}
    >
        <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
    </motion.div>
);
