'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, Upload, FileCode, Play, StopCircle, Check, X, File, Archive, Clipboard, ListChecks, Loader2, Search } from 'lucide-react';
import styles from './InputTabs.module.css';

const TABS = [
    { id: 'url', icon: <Link size={18} />, label: 'GitHub URL' },
    { id: 'zip', icon: <Upload size={18} />, label: 'Upload Files' },
    { id: 'paste', icon: <FileCode size={18} />, label: 'Paste Code' },
];

const ACCEPTED_EXTS = [
    '.zip', '.py', '.js', '.jsx', '.ts', '.tsx',
    '.go', '.java', '.rs', '.rb', '.cpp', '.c', '.h',
    '.yaml', '.yml', '.toml', '.json', '.md', '.tf',
    '.sh', '.dockerfile',
];
const ACCEPT_STR = ACCEPTED_EXTS.join(',');

export default function InputTabs({ activeSessionId, isRunning, onUrlReview, onZipReview, onPasteReview, onStop, restoredInput }) {
    const [tab, setTab] = useState('url');
    const [url, setUrl] = useState('');
    const [file, setFile] = useState(null);
    const [code, setCode] = useState('');
    const [drag, setDrag] = useState(false);
    const fileRef = useRef(null);

    // Watch for session changes to reset inputs safely
    useEffect(() => {
        if (restoredInput) {
            setTab(restoredInput.tab || 'url');
            setUrl(restoredInput.url || '');
            setCode(restoredInput.code || '');
            setFile(null);
            if (fileRef.current) fileRef.current.value = '';
        } else {
            setFile(null);
            setCode('');
            setUrl('');
            if (fileRef.current) fileRef.current.value = '';
        }
    }, [activeSessionId, restoredInput]);

    const handleSubmit = () => {
        if (isRunning) { onStop(); return; }
        if (tab === 'url' && url.trim()) onUrlReview(url.trim());
        if (tab === 'zip' && file) onZipReview(file);
        if (tab === 'paste' && code.trim()) onPasteReview(code.trim());
    };

    const canSubmit = !isRunning && (
        (tab === 'url' && url.trim()) ||
        (tab === 'zip' && file) ||
        (tab === 'paste' && code.trim())
    );

    const onDrop = (e) => {
        e.preventDefault(); setDrag(false);
        const f = e.dataTransfer.files[0];
        if (f && ACCEPTED_EXTS.some(ext =>
            f.name.toLowerCase().endsWith(ext) || f.name === 'Dockerfile' || f.name === 'Makefile'
        )) setFile(f);
    };

    return (
        <div className={`${styles.card} glass animate-in`}>
            {/* Tabs */}
            <div className={styles.tabsHeader}>
                <div className={styles.tabs}>
                    {TABS.map(t => (
                        <button
                            key={t.id}
                            className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`}
                            onClick={() => setTab(t.id)}
                            disabled={isRunning}
                            suppressHydrationWarning
                        >
                            {t.icon}
                            <span>{t.label}</span>
                            {tab === t.id && (
                                <motion.div
                                    layoutId="activeTab"
                                    className={styles.activeTabIndicator}
                                />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab content */}
            <div className={styles.body}>
                <AnimatePresence mode="wait">
                    {tab === 'url' && (
                        <motion.div
                            key="url"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className={styles.urlWrap}
                        >
                            <div className={styles.inputBox}>
                                <Link className={styles.inputIcon} size={20} />
                                <input
                                    className={styles.urlInput}
                                    type="url"
                                    value={url}
                                    onChange={e => setUrl(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && !isRunning && handleSubmit()}
                                    placeholder="Enter repository URL (e.g., https://github.com/reactjs/react)"
                                    disabled={isRunning}
                                    autoFocus
                                    suppressHydrationWarning
                                />
                            </div>
                        </motion.div>
                    )}

                    {tab === 'zip' && (
                        <motion.div
                            key="zip"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className={`${styles.dropzone} ${drag ? styles.dragover : ''} ${file ? styles.hasFile : ''}`}
                            onClick={() => !isRunning && fileRef.current?.click()}
                            onDragOver={e => { e.preventDefault(); setDrag(true); }}
                            onDragLeave={() => setDrag(false)}
                            onDrop={onDrop}
                        >
                            <input
                                ref={fileRef}
                                type="file"
                                accept={ACCEPT_STR}
                                style={{ display: 'none' }}
                                onChange={e => setFile(e.target.files[0] || null)}
                            />
                            {file ? (
                                <div className={styles.fileInfo}>
                                    <div className={styles.fileIconBox}>
                                        {file.name.endsWith('.zip') ? <Archive size={24} /> : <File size={24} />}
                                    </div>
                                    <div className={styles.fileDetails}>
                                        <div className={styles.fileName}>{file.name}</div>
                                        <div className={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</div>
                                    </div>
                                    <button
                                        className={styles.fileRemove}
                                        onClick={e => {
                                            e.stopPropagation();
                                            setFile(null);
                                            if (fileRef.current) fileRef.current.value = '';
                                        }}
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ) : (
                                <div className={styles.dropContent}>
                                    <div className={styles.dropIconBox}>
                                        <Upload size={32} />
                                    </div>
                                    <p className={styles.dropText}>Drag and drop your codebase or <span>browse files</span></p>
                                    <p className={styles.dropHint}>Supports .zip, .py, .js, .ts, .go, and 15+ other formats</p>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {tab === 'paste' && (
                        <motion.div
                            key="paste"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className={styles.pasteWrap}
                        >
                            <textarea
                                className={styles.codeArea}
                                value={code}
                                onChange={e => setCode(e.target.value)}
                                placeholder={'# Paste your code here for instant analysis...\ndef review_code(snippet):\n    return "Optimized output"'}
                                disabled={isRunning}
                                spellCheck={false}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Action Bar */}
            <div className={styles.actionBar}>
                <button
                    className={`${styles.btn} ${isRunning ? styles.btnStop : canSubmit ? styles.btnReady : ''}`}
                    onClick={handleSubmit}
                    disabled={!isRunning && !canSubmit}
                    suppressHydrationWarning
                >
                    {isRunning ? (
                        <>
                            <StopCircle size={18} />
                            <span>Interrupt Analysis</span>
                        </>
                    ) : (
                        <>
                            <Play size={18} />
                            <span>Execute Multi-Agent Review</span>
                        </>
                    )}
                </button>

                {canSubmit && !isRunning && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className={styles.readyBadge}
                    >
                        <Check size={12} /> <span>Ready</span>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
