import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export const GlassPanel = ({ children, className, title, icon: Icon }) => {
    return (
        <div className={cn(
            "glass border border-white/10 rounded-xl overflow-hidden flex flex-col backdrop-blur-md bg-void/50 shadow-2xl transition-all duration-300",
            className
        )}>
            {(title || Icon) && (
                <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 bg-white/5">
                    {Icon && <Icon className="w-4 h-4 text-blue-400" />}
                    {title && <h3 className="text-xs font-semibold uppercase tracking-wider text-white/70">{title}</h3>}
                </div>
            )}
            <div className="flex-1 overflow-auto">
                {children}
            </div>
        </div>
    );
};
