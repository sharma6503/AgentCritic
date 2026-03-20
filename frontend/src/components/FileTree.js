import React, { useState } from 'react';
import { Folder, File, ChevronRight, ChevronDown } from 'lucide-react';

const FileItem = ({ item, depth = 0, onSelect }) => {
    const [isOpen, setIsOpen] = useState(false);
    const isFolder = item.type === 'directory' || (item.children && item.children.length > 0);

    return (
        <div className="select-none">
            <div
                className="flex items-center py-1 px-2 hover:bg-white/5 cursor-pointer rounded transition-colors group"
                style={{ paddingLeft: `${depth * 12 + 8}px` }}
                onClick={() => {
                    if (isFolder) setIsOpen(!isOpen);
                    else if (onSelect) onSelect(item.path);
                }}
            >
                <span className="mr-1.5 text-text-muted group-hover:text-blue-400 transition-colors">
                    {isFolder ? (
                        isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
                    ) : (
                        <div className="w-4" />
                    )}
                </span>
                <span className="mr-2">
                    {isFolder ? (
                        <Folder className="w-4 h-4 text-blue-400/80" />
                    ) : (
                        <File className="w-4 h-4 text-text-muted/80" />
                    )}
                </span>
                <span className="text-xs text-text-secondary group-hover:text-text-primary transition-colors truncate">
                    {item.name}
                </span>
            </div>
            {isFolder && isOpen && (
                <div>
                    {item.children.map((child, idx) => (
                        <FileItem key={idx} item={child} depth={depth + 1} onSelect={onSelect} />
                    ))}
                </div>
            )}
        </div>
    );
};

export const FileTree = ({ data, onSelect }) => {
    if (!data || data.length === 0) return (
        <div className="p-4 text-xs text-text-muted italic">No files loaded.</div>
    );

    return (
        <div className="py-2">
            {data.map((item, idx) => (
                <FileItem key={idx} item={item} onSelect={onSelect} />
            ))}
        </div>
    );
};
