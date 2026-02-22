'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, FileText, AlertTriangle, ShieldCheck, Activity, Terminal } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import styles from './ReviewAccordion.module.css';

const SECTION_ICONS = {
    'Executive Summary': <FileText size={18} />,
    'Code Quality': <Activity size={18} />,
    'Security': <ShieldCheck size={18} />,
    'Architecture': <Terminal size={18} />,
    'Vulnerabilities': <AlertTriangle size={18} />,
};

function AccordionItem({ title, content, isOpen, onToggle }) {
    // Determine icon based on title keywords
    const iconKey = Object.keys(SECTION_ICONS).find(k => title.toLowerCase().includes(k.toLowerCase())) || 'Executive Summary';
    const Icon = SECTION_ICONS[iconKey] || SECTION_ICONS['Executive Summary'];

    return (
        <div className={`${styles.item} ${isOpen ? styles.itemOpen : ''}`}>
            <button className={styles.trigger} onClick={onToggle}>
                <div className={styles.triggerLeft}>
                    <span className={styles.iconBox}>{Icon}</span>
                    <span className={styles.title}>{title}</span>
                </div>
                <ChevronDown className={`${styles.chevron} ${isOpen ? styles.chevronUp : ''}`} size={20} />
            </button>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                        className={styles.contentWrap}
                    >
                        <div className={`${styles.content} md`}>
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                rehypePlugins={[rehypeHighlight]}
                            >
                                {content}
                            </ReactMarkdown>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default function ReviewAccordion({ content }) {
    const [openIndices, setOpenIndices] = useState([0]); // Open first by default

    if (!content) return null;

    // Split markdown by '## ' (H2 headers)
    const sections = [];
    const parts = content.split(/^##\s+/m);

    // First part is usually the title or intro (everything before first H2)
    const intro = parts[0].trim();
    if (intro) {
        sections.push({ title: 'Overview', content: intro });
    }

    for (let i = 1; i < parts.length; i++) {
        const lines = parts[i].split('\n');
        const title = lines[0].trim();
        const body = lines.slice(1).join('\n').trim();
        if (title && body) {
            sections.push({ title, content: body });
        }
    }

    const toggle = (idx) => {
        setOpenIndices(prev =>
            prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
        );
    };

    return (
        <div className={styles.accordion}>
            {sections.map((sec, idx) => (
                <AccordionItem
                    key={idx}
                    title={sec.title}
                    content={sec.content}
                    isOpen={openIndices.includes(idx)}
                    onToggle={() => toggle(idx)}
                />
            ))}
        </div>
    );
}
