// Node colors by type
export const NODE_COLORS = {
  Project: '#a855f7',
  Package: '#8b5cf6',
  Module: '#7c3aed',
  Folder: '#6366f1',
  File: '#3b82f6',
  Class: '#f59e0b',
  Function: '#10b981',
  Method: '#14b8a6',
  Variable: '#64748b',
  Interface: '#ec4899',
  Enum: '#f97316',
  Decorator: '#eab308',
  Import: '#475569',
  Type: '#a78bfa',
  CodeElement: '#64748b',
  Community: '#818cf8',
  Process: '#f43f5e',
};

// Node sizes by type
export const NODE_SIZES = {
  Project: 20,
  Package: 16,
  Module: 13,
  Folder: 10,
  File: 6,
  Class: 8,
  Function: 4,
  Method: 3,
  Variable: 2,
  Interface: 7,
  Enum: 5,
  Decorator: 2,
  Import: 1.5,
  Type: 3,
  CodeElement: 2,
  Community: 0,
  Process: 0,
};

export const COMMUNITY_COLORS = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4',
  '#3b82f6', '#8b5cf6', '#d946ef', '#ec4899', '#f43f5e',
  '#14b8a6', '#84cc16',
];

export const getCommunityColor = (communityIndex) => {
  return COMMUNITY_COLORS[communityIndex % COMMUNITY_COLORS.length];
};

export const DEFAULT_VISIBLE_LABELS = [
  'Project', 'Package', 'Module', 'Folder', 'File',
  'Class', 'Function', 'Method', 'Interface', 'Enum', 'Type',
];

export const FILTERABLE_LABELS = [
  'Folder', 'File', 'Class', 'Function', 'Method',
  'Variable', 'Interface', 'Import',
];

export const ALL_EDGE_TYPES = [
  'CONTAINS', 'DEFINES', 'IMPORTS', 'CALLS', 'EXTENDS', 'IMPLEMENTS',
];

export const DEFAULT_VISIBLE_EDGES = [
  'CONTAINS', 'DEFINES', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS', 'CALLS',
];

export const EDGE_INFO = {
  CONTAINS: { color: '#2d5a3d', label: 'Contains' },
  DEFINES: { color: '#0e7490', label: 'Defines' },
  IMPORTS: { color: '#1d4ed8', label: 'Imports' },
  CALLS: { color: '#7c3aed', label: 'Calls' },
  EXTENDS: { color: '#c2410c', label: 'Extends' },
  IMPLEMENTS: { color: '#be185d', label: 'Implements' },
};
