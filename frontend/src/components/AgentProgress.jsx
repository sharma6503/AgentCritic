import styles from './AgentProgress.module.css';

export default function AgentProgress({ label }) {
    return (
        <div className={styles.bar}>
            <div className={styles.track}>
                <div className={styles.fill} />
            </div>
            <span className={styles.spinner} />
            <span className={styles.label}>{label}</span>
        </div>
    );
}
