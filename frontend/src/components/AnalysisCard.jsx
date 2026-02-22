'use client';

import styles from './AnalysisCard.module.css';

// Severity colour map
const SEV_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
    low: '#10b981',
};
const CAT_COLORS = {
    adk: '#3b82f6',
    quality: '#8b5cf6',
    security: '#ef4444',
    validation: '#06b6d4',
};
const CAT_LABELS = {
    adk: '🏗️ ADK',
    quality: '🧹 Quality',
    security: '🔒 Security',
    validation: '🧪 Validation',
};

// SVG Donut chart
function Donut({ data, total }) {
    const SIZE = 120;
    const R = 46;
    const CX = 60; const CY = 60;
    const circ = 2 * Math.PI * R;

    // Compute segments
    const segments = [];
    let offset = -0.25 * circ; // start at top

    const entries = Object.entries(data);
    const hasData = total > 0;

    if (!hasData) {
        // Gray empty state ring
        segments.push(
            <circle key="empty" cx={CX} cy={CY} r={R}
                fill="none" stroke="#e2e8f0" strokeWidth="14" />
        );
    } else {
        entries.forEach(([key, val]) => {
            const pct = val / total;
            const dash = pct * circ;
            if (dash < 0.5) { offset += dash; return; }
            segments.push(
                <circle
                    key={key}
                    cx={CX} cy={CY} r={R}
                    fill="none"
                    stroke={SEV_COLORS[key]}
                    strokeWidth="14"
                    strokeDasharray={`${dash} ${circ - dash}`}
                    strokeDashoffset={-offset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dasharray 0.6s ease' }}
                />
            );
            offset += dash;
        });
    }

    // Score colour
    const score = Math.min(100, Math.max(0, Math.round(
        entries.reduce((acc, [k, v]) => {
            const penalty = { critical: 15, high: 8, medium: 3, low: 1 };
            return acc - (penalty[k] || 0) * v;
        }, 100)
    )));

    return (
        <div className={styles.donutWrap}>
            <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
                <circle cx={CX} cy={CY} r={R} fill="none" stroke="#eff6ff" strokeWidth="14" />
                {segments}
                <text x={CX} y={CY - 6} textAnchor="middle" fontSize="18" fontWeight="800"
                    fill={total === 0 ? '#94a3b8' : '#1d4ed8'}>
                    {total}
                </text>
                <text x={CX} y={CY + 10} textAnchor="middle" fontSize="8.5" fill="#64748b"
                    fontWeight="500" letterSpacing="0.05em">
                    {total === 1 ? 'ISSUE' : 'ISSUES'}
                </text>
            </svg>
        </div>
    );
}

export default function AnalysisCard({ metrics }) {
    if (!metrics) return null;

    const { severity = {}, category = {}, total = 0, score = 0 } = metrics;
    const clampedScore = Math.min(100, Math.max(0, score));

    const scoreColor =
        clampedScore >= 80 ? '#10b981' :
            clampedScore >= 60 ? '#f59e0b' :
                clampedScore >= 40 ? '#f97316' : '#ef4444';

    const scoreLabel =
        clampedScore >= 80 ? 'Good' :
            clampedScore >= 60 ? 'Fair' :
                clampedScore >= 40 ? 'Poor' : 'Critical';

    const catMax = Math.max(1, ...Object.values(category));

    return (
        <div className={`${styles.card} corner-card corner-card-inner`}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <span className={styles.headerDot} />
                    <span className={styles.headerTitle}>ERROR ANALYSIS</span>
                </div>
                <span className={styles.badge}>
                    {total} {total === 1 ? 'issue' : 'issues'} found
                </span>
            </div>

            <div className={styles.body}>
                {/* Score + Donut row */}
                <div className={styles.topRow}>

                    {/* Quality Score */}
                    <div className={styles.scoreBox}>
                        <div className={styles.scoreNum} style={{ color: scoreColor }}>
                            {clampedScore}
                        </div>
                        <div className={styles.scoreLabel}>Quality Score</div>
                        <div className={styles.scoreBar}>
                            <div
                                className={styles.scoreFill}
                                style={{ width: `${clampedScore}%`, background: scoreColor }}
                            />
                        </div>
                        <div className={styles.scoreVerdict} style={{ color: scoreColor }}>
                            {scoreLabel}
                        </div>
                    </div>

                    {/* Donut */}
                    <Donut data={severity} total={total} />

                    {/* Severity legend */}
                    <div className={styles.legend}>
                        {Object.entries(severity).map(([key, val]) => (
                            <div key={key} className={styles.legendItem}>
                                <span
                                    className={styles.legendDot}
                                    style={{ background: SEV_COLORS[key] }}
                                />
                                <span className={styles.legendKey}>{key}</span>
                                <span className={styles.legendVal}
                                    style={{ color: val > 0 ? SEV_COLORS[key] : '#94a3b8' }}>
                                    {val}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Divider */}
                <div className={styles.divider} />

                {/* Category bars */}
                <div className={styles.catSection}>
                    <div className={styles.catTitle}>Issues by Category</div>
                    <div className={styles.bars}>
                        {Object.entries(category).map(([key, val]) => (
                            <div key={key} className={styles.barRow}>
                                <span className={styles.barLabel}>{CAT_LABELS[key] ?? key}</span>
                                <div className={styles.barTrack}>
                                    <div
                                        className={styles.barFill}
                                        style={{
                                            width: `${Math.round((val / catMax) * 100)}%`,
                                            background: CAT_COLORS[key] ?? '#3b82f6',
                                        }}
                                    />
                                </div>
                                <span className={styles.barCount}
                                    style={{ color: val > 0 ? CAT_COLORS[key] : '#94a3b8' }}>
                                    {val}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
