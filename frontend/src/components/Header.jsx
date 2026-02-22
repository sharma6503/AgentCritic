import { motion } from 'framer-motion';
import { Bot, Shield, Zap, CheckCircle, Cpu } from 'lucide-react';
import styles from './Header.module.css';

export default function Header({ isRunning, activeSessionId }) {
    return (
        <header className={`${styles.wrap} glass`}>
            <div className={styles.inner}>
                {/* Logo + name */}
                <motion.div
                    className={styles.brand}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <div className={styles.logoBox}>
                        <Cpu className={styles.logoIcon} size={28} />
                    </div>
                    <div>
                        <div className={styles.name}>
                            <span className={styles.namePrefix}>im.</span>
                            <span className={styles.nameMiddle}>agentic.</span>
                            <span className={styles.nameSuffix}>review.ai</span>
                        </div>
                        <div className={styles.sub}>
                            Multi-agent code review · powered by Google ADK
                            {activeSessionId && (
                                <span className={styles.sessionId} title="Active Session ID">
                                    &nbsp;|&nbsp;Session: <code style={{ fontSize: '0.85em', opacity: 0.8 }}>{activeSessionId.substring(0, 8)}</code>
                                </span>
                            )}
                        </div>
                    </div>
                </motion.div>

                {/* Status + pills */}
                <div className={styles.meta}>
                    <motion.div
                        className={`${styles.badge} ${isRunning ? styles.badgeLive : ''}`}
                        animate={isRunning ? { scale: [1, 1.05, 1] } : {}}
                        transition={{ repeat: Infinity, duration: 2 }}
                    >
                        <span className={styles.pulseDot} />
                        {isRunning ? 'Reviewing…' : 'Ready'}
                    </motion.div>

                    <div className={styles.pills}>
                        <div className={styles.pill}>
                            <Bot size={14} /> <span>ADK</span>
                        </div>
                        <div className={styles.pill}>
                            <Shield size={14} /> <span>Security</span>
                        </div>
                        <div className={styles.pill}>
                            <Zap size={14} /> <span>Quality</span>
                        </div>
                        <div className={styles.pill}>
                            <CheckCircle size={14} /> <span>Validation</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
