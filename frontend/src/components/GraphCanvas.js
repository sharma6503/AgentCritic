'use client';

import React, { useEffect, useCallback, useMemo, useState, forwardRef, useImperativeHandle } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Focus, RotateCcw, Play, Pause, Lightbulb, LightbulbOff } from 'lucide-react';
import { useSigma } from '../hooks/useSigma';
import { knowledgeGraphToGraphology, filterGraphByDepth } from '../lib/graph-adapter';

export const GraphCanvas = forwardRef(({
    graphData,
    onNodeSelect,
    selectedNodeId,
    highlightedNodeIds = new Set(),
    animatedNodes = new Map(),
    blastRadiusNodeIds = new Set(),
    visibleLabels = ['Project', 'Package', 'Module', 'Folder', 'File', 'Class', 'Function', 'Method', 'Interface', 'Enum', 'Type'],
    visibleEdgeTypes = ['CONTAINS', 'DEFINES', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS', 'CALLS'],
    depthFilter = null
}, ref) => {
    const [hoveredNodeName, setHoveredNodeName] = useState(null);
    const [isAIHighlightsEnabled, setIsAIHighlightsEnabled] = useState(true);

    // Filter effect based on AI highlights wrapper
    const effectiveHighlightedNodeIds = useMemo(() => {
        if (!isAIHighlightsEnabled) return new Set();
        return highlightedNodeIds;
    }, [highlightedNodeIds, isAIHighlightsEnabled]);

    const effectiveBlastRadiusNodeIds = useMemo(() => {
        if (!isAIHighlightsEnabled) return new Set();
        return blastRadiusNodeIds;
    }, [blastRadiusNodeIds, isAIHighlightsEnabled]);

    const effectiveAnimatedNodes = useMemo(() => {
        if (!isAIHighlightsEnabled) return new Map();
        return animatedNodes;
    }, [animatedNodes, isAIHighlightsEnabled]);

    const handleNodeClick = useCallback((nodeId) => {
        if (!graphData) return;
        const node = graphData.nodes.find(n => n.id === nodeId);
        if (node && onNodeSelect) {
            onNodeSelect(node);
        }
    }, [graphData, onNodeSelect]);

    const handleNodeHover = useCallback((nodeId) => {
        if (!nodeId || !graphData) {
            setHoveredNodeName(null);
            return;
        }
        const node = graphData.nodes.find(n => n.id === nodeId);
        if (node) setHoveredNodeName(node.properties?.name || node.label);
    }, [graphData]);

    const handleStageClick = useCallback(() => {
        if (onNodeSelect) onNodeSelect(null);
    }, [onNodeSelect]);

    const {
        containerRef,
        sigmaRef,
        setGraph: setSigmaGraph,
        zoomIn,
        zoomOut,
        resetZoom,
        focusNode,
        isLayoutRunning,
        startLayout,
        stopLayout,
        selectedNode: sigmaSelectedNode,
        setSelectedNode: setSigmaSelectedNode,
    } = useSigma({
        onNodeClick: handleNodeClick,
        onNodeHover: handleNodeHover,
        onStageClick: handleStageClick,
        highlightedNodeIds: effectiveHighlightedNodeIds,
        blastRadiusNodeIds: effectiveBlastRadiusNodeIds,
        animatedNodes: effectiveAnimatedNodes,
        visibleEdgeTypes,
    });

    useImperativeHandle(ref, () => ({
        focusNode: (nodeId) => {
            if (graphData) {
                const node = graphData.nodes.find(n => n.id === nodeId);
                if (node && onNodeSelect) {
                    onNodeSelect(node);
                }
            }
            focusNode(nodeId);
        }
    }), [focusNode, graphData, onNodeSelect]);

    // Transform graph data whenever it changes
    useEffect(() => {
        if (!graphData) return;

        // Build community members
        const communityMemberships = new Map();
        graphData.relationships.forEach(rel => {
            if (rel.type === 'MEMBER_OF') {
                const communityNode = graphData.nodes.find(n => n.id === rel.targetId && n.label === 'Community');
                if (communityNode) {
                    const communityIdx = parseInt(rel.targetId.replace('comm_', ''), 10) || 0;
                    communityMemberships.set(rel.sourceId, communityIdx);
                }
            }
        });

        const sigmaGraph = knowledgeGraphToGraphology(graphData, communityMemberships);
        setSigmaGraph(sigmaGraph);
    }, [graphData, setSigmaGraph]);

    // Adjust filters
    useEffect(() => {
        const sigma = sigmaRef.current;
        if (!sigma) return;
        const sigmaGraph = sigma.getGraph();
        if (sigmaGraph.order === 0) return;
        filterGraphByDepth(sigmaGraph, selectedNodeId || null, depthFilter, visibleLabels);
        sigma.refresh();
    }, [visibleLabels, depthFilter, selectedNodeId, sigmaRef]);

    // Sync selected node prop to sigma selection
    useEffect(() => {
        setSigmaSelectedNode(selectedNodeId || null);
    }, [selectedNodeId, setSigmaSelectedNode]);

    const handleFocusSelected = useCallback(() => {
        if (selectedNodeId) {
            focusNode(selectedNodeId);
        }
    }, [selectedNodeId, focusNode]);

    const handleClearSelection = useCallback(() => {
        if (onNodeSelect) onNodeSelect(null);
        setSigmaSelectedNode(null);
        resetZoom();
    }, [onNodeSelect, setSigmaSelectedNode, resetZoom]);

    const toggleAIHighlights = () => setIsAIHighlightsEnabled(v => !v);

    // Get currently selected node obj
    const selectedNodeObj = graphData ? graphData.nodes.find(n => n.id === selectedNodeId) : null;

    return (
        <div className="relative w-full h-full" style={{ backgroundColor: '#06060a', overflow: 'hidden' }}>
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    background: `
            radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.03) 0%, transparent 70%),
            linear-gradient(to bottom, #06060a, #0a0a10)
          `
                }}
            />
            <div
                ref={containerRef}
                className="sigma-container w-full h-full cursor-grab active:cursor-grabbing"
            />

            {hoveredNodeName && !sigmaSelectedNode && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 px-3 py-1.5 border rounded-lg backdrop-blur-sm z-20 pointer-events-none" style={{ background: 'rgba(20, 20, 30, 0.95)', borderColor: '#3a3a4a' }}>
                    <span className="font-mono text-sm text-gray-200">{hoveredNodeName}</span>
                </div>
            )}

            {sigmaSelectedNode && selectedNodeObj && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 border rounded-xl backdrop-blur-sm z-20 animate-in fade-in slide-in-from-bottom-2" style={{ background: 'rgba(124, 58, 237, 0.2)', borderColor: 'rgba(124, 58, 237, 0.3)' }}>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#c084fc' }} />
                    <span className="font-mono text-sm text-gray-200">
                        {selectedNodeObj.properties?.name || selectedNodeObj.label}
                    </span>
                    <span className="text-xs text-gray-400">
                        ({selectedNodeObj.label})
                    </span>
                    <button
                        onClick={handleClearSelection}
                        className="ml-2 px-2 py-0.5 text-xs text-gray-400 hover:text-white rounded transition-colors"
                    >
                        Clear
                    </button>
                </div>
            )}

            <div className="absolute bottom-4 right-4 flex flex-col gap-1 z-10">
                <button onClick={zoomIn} className="w-9 h-9 flex items-center justify-center border rounded-md text-gray-400 hover:text-white transition-colors" style={{ background: '#1c1c28', borderColor: '#333342' }} title="Zoom In"><ZoomIn className="w-4 h-4" /></button>
                <button onClick={zoomOut} className="w-9 h-9 flex items-center justify-center border rounded-md text-gray-400 hover:text-white transition-colors" style={{ background: '#1c1c28', borderColor: '#333342' }} title="Zoom Out"><ZoomOut className="w-4 h-4" /></button>
                <button onClick={resetZoom} className="w-9 h-9 flex items-center justify-center border rounded-md text-gray-400 hover:text-white transition-colors" style={{ background: '#1c1c28', borderColor: '#333342' }} title="Fit to Screen"><Maximize2 className="w-4 h-4" /></button>

                <div className="h-px bg-gray-800 my-1" />

                {selectedNodeId && (
                    <button onClick={handleFocusSelected} className="w-9 h-9 flex items-center justify-center border rounded-md transition-colors" style={{ background: 'rgba(124, 58, 237, 0.2)', borderColor: 'rgba(124, 58, 237, 0.3)', color: '#c084fc' }} title="Focus on Selected Node">
                        <Focus className="w-4 h-4" />
                    </button>
                )}

                {sigmaSelectedNode && (
                    <button onClick={handleClearSelection} className="w-9 h-9 flex items-center justify-center border rounded-md text-gray-400 hover:text-white transition-colors" style={{ background: '#1c1c28', borderColor: '#333342' }} title="Clear Selection">
                        <RotateCcw className="w-4 h-4" />
                    </button>
                )}

                <div className="h-px bg-gray-800 my-1" />

                <button
                    onClick={isLayoutRunning ? stopLayout : startLayout}
                    className={`w-9 h-9 flex items-center justify-center border rounded-md transition-all ${isLayoutRunning ? 'animate-pulse' : ''}`}
                    style={isLayoutRunning ? { background: '#7c3aed', borderColor: '#7c3aed', color: '#fff' } : { background: '#1c1c28', borderColor: '#333342', color: '#9ca3af' }}
                    title={isLayoutRunning ? 'Stop Layout' : 'Run Layout Again'}
                >
                    {isLayoutRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
            </div>

            <div className="absolute top-4 right-4 z-20">
                <button
                    onClick={toggleAIHighlights}
                    className="w-10 h-10 flex items-center justify-center border rounded-lg transition-colors"
                    style={isAIHighlightsEnabled ? { background: 'rgba(6, 182, 212, 0.15)', borderColor: 'rgba(34, 211, 238, 0.4)', color: '#a5f3fc' } : { background: '#1c1c28', borderColor: '#333342', color: '#9ca3af' }}
                    title={isAIHighlightsEnabled ? 'Turn off all highlights' : 'Turn on AI highlights'}
                >
                    {isAIHighlightsEnabled ? <Lightbulb className="w-4 h-4" /> : <LightbulbOff className="w-4 h-4" />}
                </button>
            </div>
        </div>
    );
});

GraphCanvas.displayName = 'GraphCanvas';
