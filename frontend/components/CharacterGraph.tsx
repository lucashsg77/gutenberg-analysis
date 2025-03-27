import React, { useRef, useEffect, useState, useCallback } from 'react';
import { GraphData, GraphNode } from '@/types';

interface CharacterGraphProps {
  graphData: GraphData;
}

interface ProcessedNode extends GraphNode {
  color: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface ProcessedLink {
  source: number;
  target: number;
  value: number;
  type: string;
}

interface ProcessedGraphData {
  nodes: ProcessedNode[];
  links: ProcessedLink[];
}

interface Transform {
  scale: number;
  translateX: number;
  translateY: number;
}

const CharacterGraph: React.FC<CharacterGraphProps> = ({ graphData }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [tooltipNode, setTooltipNode] = useState<{ node: GraphNode, x: number, y: number } | null>(null);
  const [tooltipLink, setTooltipLink] = useState<{ source: string, target: string, type: string, x: number, y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragNode, setDragNode] = useState<number | null>(null);
  const [processedData, setProcessedData] = useState<ProcessedGraphData | null>(null);
  const animationRef = useRef<number | null>(null);

  const [transform, setTransform] = useState<Transform>({ scale: 1, translateX: 0, translateY: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!graphData || !graphData.nodes || !graphData.links) {
      console.warn("Missing or invalid graph data:", graphData);
      return;
    }
    
    console.log("Processing graph data:", {
      nodes: graphData.nodes.length,
      links: graphData.links.length
    });
    
    const width = dimensions.width;
    const height = dimensions.height;

    const nodes = graphData.nodes.map((node) => ({
      ...node,
      color: getNodeColor(node.role),
      x: width / 2 + (Math.random() - 0.5) * 200,
      y: height / 2 + (Math.random() - 0.5) * 200,
      vx: 0,
      vy: 0
    }));

    const nodeIndices = new Map();
    nodes.forEach((node, index) => {
      nodeIndices.set(node.id, index);
    });

    console.log("Node IDs in graph:", nodes.map(node => node.id));

    const links = graphData.links
      .map(link => {
        const sourceId = String(link.source);
        const targetId = String(link.target);
        
        console.log(`Processing link: ${sourceId} → ${targetId} (${link.type})`);
        
        if (!nodeIndices.has(sourceId)) {
          console.warn(`Link source node not found: ${sourceId}`);
          return null;
        }
        if (!nodeIndices.has(targetId)) {
          console.warn(`Link target node not found: ${targetId}`);
          return null;
        }
        
        return {
          ...link,
          source: nodeIndices.get(sourceId),
          target: nodeIndices.get(targetId),
          value: link.value || 2,
          type: link.type || 'relationship'
        };
      })
      .filter(link => link !== null) as ProcessedLink[];

    console.log("Processed links:", links.map(l => `${l.source}->${l.target} (${l.type})`));

    console.log("Processed data:", {
      nodes: nodes.length,
      links: links.length,
      nodeIds: nodes.map(n => n.id),
      nodeIndices: Array.from(nodeIndices.entries())
    });

    setProcessedData({ nodes, links });
  }, [graphData, dimensions]);

  useEffect(() => {
    if (containerRef.current) {
      const updateDimensions = () => {
        if (containerRef.current) {
          const { width, height } = containerRef.current.getBoundingClientRect();
          setDimensions({
            width: width,
            height: Math.max(500, height)
          });
          
          if (canvasRef.current) {
            canvasRef.current.width = width;
            canvasRef.current.height = Math.max(500, height);
          }
        }
      };

      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;

    const screenToGraph = (screenX: number, screenY: number) => {
      return {
        x: (screenX - transform.translateX) / transform.scale,
        y: (screenY - transform.translateY) / transform.scale
      };
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!canvas) return;
      
      const rect = canvas.getBoundingClientRect();
      const screenX = e.clientX - rect.left;
      const screenY = e.clientY - rect.top;

      if (isPanning) {
        const dx = screenX - lastMousePos.x;
        const dy = screenY - lastMousePos.y;
        
        setTransform(prev => ({
          ...prev,
          translateX: prev.translateX + dx,
          translateY: prev.translateY + dy
        }));
        
        setLastMousePos({ x: screenX, y: screenY });
        return;
      }

      const { x, y } = screenToGraph(screenX, screenY);
      
      if (isDragging && dragNode !== null && processedData) {
        const node = processedData.nodes[dragNode];
        if (node) {
          node.x = x;
          node.y = y;
          node.vx = 0;
          node.vy = 0;
        }
      } else {
        if (processedData) {
          let hoveredNode = null;
          for (let i = 0; i < processedData.nodes.length; i++) {
            const node = processedData.nodes[i];
            const dx = node.x - x;
            const dy = node.y - y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const nodeRadius = (node.size / 2) + 4;
            
            if (distance < nodeRadius) {
              const screenNodeX = node.x * transform.scale + transform.translateX;
              const screenNodeY = node.y * transform.scale + transform.translateY;
              hoveredNode = { node, x: screenNodeX, y: screenNodeY };
              break;
            }
          }
          
          if (hoveredNode) {
            setTooltipNode(hoveredNode);
            setTooltipLink(null);
          } else {
            let hoveredLink = null;
            for (let i = 0; i < processedData.links.length; i++) {
              const link = processedData.links[i];
              const source = processedData.nodes[link.source];
              const target = processedData.nodes[link.target];

              if (!source || !target) continue;

              const A = x - source.x;
              const B = y - source.y;
              const C = target.x - source.x;
              const D = target.y - source.y;
              
              const dot = A * C + B * D;
              const len_sq = C * C + D * D;
              let param = -1;
              
              if (len_sq !== 0) param = dot / len_sq;
              
              let xx, yy;
              
              if (param < 0) {
                xx = source.x;
                yy = source.y;
              } else if (param > 1) {
                xx = target.x;
                yy = target.y;
              } else {
                xx = source.x + param * C;
                yy = source.y + param * D;
              }
              
              const dx = x - xx;
              const dy = y - yy;
              const distance = Math.sqrt(dx * dx + dy * dy);

              const detectionRadius = 5 / transform.scale;
              
              if (distance < detectionRadius) {
                const midX = (source.x + target.x) / 2;
                const midY = (source.y + target.y) / 2;
                const screenMidX = midX * transform.scale + transform.translateX;
                const screenMidY = midY * transform.scale + transform.translateY;
                
                hoveredLink = {
                  source: source.id as string,
                  target: target.id as string,
                  type: link.type,
                  x: screenMidX,
                  y: screenMidY
                };
                break;
              }
            }
            
            if (hoveredLink) {
              setTooltipNode(null);
              setTooltipLink(hoveredLink);
            } else {
              setTooltipNode(null);
              setTooltipLink(null);
            }
          }
        }
      }
    };
    
    const handleMouseDown = (e: MouseEvent) => {
      if (!canvas || !processedData) return;
      
      const rect = canvas.getBoundingClientRect();
      const screenX = e.clientX - rect.left;
      const screenY = e.clientY - rect.top;

      if (e.buttons === 4 || (e.buttons === 1 && e.altKey)) {
        setIsPanning(true);
        setLastMousePos({ x: screenX, y: screenY });
        return;
      }

      const { x, y } = screenToGraph(screenX, screenY);

      for (let i = 0; i < processedData.nodes.length; i++) {
        const node = processedData.nodes[i];
        const dx = node.x - x;
        const dy = node.y - y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const nodeRadius = (node.size / 2) + 4;
        
        if (distance < nodeRadius) {
          setIsDragging(true);
          setDragNode(i);
          break;
        }
      }
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      setDragNode(null);
      setIsPanning(false);
    };
    
    const handleWheel = (e: WheelEvent) => {
      if (!canvas) return;
      
      e.preventDefault();
      
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const delta = e.deltaY < 0 ? 1.1 : 0.9;
      const newScale = transform.scale * delta;

      if (newScale < 0.1 || newScale > 10) return;

      const scaleRatio = 1 - delta;
      const translateX = transform.translateX + scaleRatio * (mouseX - transform.translateX);
      const translateY = transform.translateY + scaleRatio * (mouseY - transform.translateY);
      
      setTransform({
        scale: newScale,
        translateX,
        translateY
      });
    };
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'r' || e.key === 'R') {
        setTransform({ scale: 1, translateX: 0, translateY: 0 });
      }

      if (e.key === 'Alt' && isPanning === false) {
        setIsPanning(true);
        if (canvas) {
          const rect = canvas.getBoundingClientRect();
          setLastMousePos({ 
            x: rect.width / 2, 
            y: rect.height / 2 
          });
        }
      }
    };
    
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Alt') {
        setIsPanning(false);
      }
    };

    canvas?.addEventListener('wheel', handleWheel, { passive: false });
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      canvas?.removeEventListener('wheel', handleWheel);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [processedData, isDragging, dragNode, transform, isPanning, lastMousePos]);
  
  const render = useCallback(() => {
    if (!canvasRef.current || !processedData) return;
  
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
  
    const width = dimensions.width;
    const height = dimensions.height;

    ctx.clearRect(0, 0, width, height);

    ctx.save();
    ctx.translate(transform.translateX, transform.translateY);
    ctx.scale(transform.scale, transform.scale);

    console.log("Drawing links:", processedData.links.length);

    for (const link of processedData.links) {
      const source = processedData.nodes[link.source];
      const target = processedData.nodes[link.target];
  
      if (!source || !target) {
        console.warn(`Missing node for link: source=${link.source}, target=${link.target}`);
        continue;
      }

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);

      ctx.strokeStyle = link.type === 'Friend' ? 'rgba(50, 205, 50, 0.9)' : 'rgba(255, 165, 0, 0.9)';
      ctx.lineWidth = Math.max(2, Math.min(link.value, 4)) / transform.scale;
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.lineWidth = (Math.max(3, Math.min(link.value, 5)) + 2) / transform.scale;
      ctx.stroke();
    }

    for (const node of processedData.nodes) {
      const nodeSize = Math.max(8, (node.size / 2) + 4) / transform.scale;
  
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
      ctx.fillStyle = node.color;
      ctx.fill();
  
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5 / transform.scale;
      ctx.stroke();
  
      const label = String(node.id);
      ctx.font = `${12 / transform.scale}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
  
      const textWidth = ctx.measureText(label).width;
  
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(
        node.x - textWidth / 2 - 2 / transform.scale,
        node.y + nodeSize + 2 / transform.scale,
        textWidth + 4 / transform.scale,
        14 / transform.scale
      );
  
      ctx.fillStyle = 'white';
      ctx.fillText(label, node.x, node.y + nodeSize + 8 / transform.scale);
    }

    ctx.restore();

    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.font = '10px Sans-Serif';
    ctx.fillText(`Zoom: ${Math.round(transform.scale * 100)}%`, 10, height - 10);
    
  }, [processedData, dimensions, transform]);

  useEffect(() => {
    if (!processedData || processedData.nodes.length === 0) return;
    
    const simulateForces = () => {
      const nodes = processedData.nodes;
      const links = processedData.links;
      const width = dimensions.width;
      const height = dimensions.height;

      for (let i = 0; i < nodes.length; i++) {
        if (dragNode === i) continue;
        
        const node = nodes[i];

        node.vx += (width / 2 - node.x) * 0.005;
        node.vy += (height / 2 - node.y) * 0.005;

        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          
          const otherNode = nodes[j];
          const dx = node.x - otherNode.x;
          const dy = node.y - otherNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const forceMagnitude = 1000 / (dist * dist);
          
          node.vx += (dx / dist) * forceMagnitude;
          node.vy += (dy / dist) * forceMagnitude;
        }
      }

      for (const link of links) {
        if (link.source >= nodes.length || link.target >= nodes.length) {
          console.warn(`Invalid link indices: source=${link.source}, target=${link.target}, nodes.length=${nodes.length}`);
          continue;
        }
        
        const source = nodes[link.source];
        const target = nodes[link.target];
        
        if (!source || !target) {
          console.warn('Missing source or target node for link');
          continue;
        }
        
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const forceMagnitude = (dist - 100) * 0.03 * Math.min(link.value, 10);
        
        if (dragNode !== link.source) {
          source.vx += (dx / dist) * forceMagnitude;
          source.vy += (dy / dist) * forceMagnitude;
        }
        
        if (dragNode !== link.target) {
          target.vx -= (dx / dist) * forceMagnitude;
          target.vy -= (dy / dist) * forceMagnitude;
        }
      }

      for (let i = 0; i < nodes.length; i++) {
        if (dragNode === i) continue;
        
        const node = nodes[i];
        node.x += node.vx;
        node.y += node.vy;
        node.vx *= 0.9;
        node.vy *= 0.9;

        node.x = Math.max(20, Math.min(width - 20, node.x));
        node.y = Math.max(20, Math.min(height - 20, node.y));
      }

      render();

      animationRef.current = requestAnimationFrame(simulateForces);
    };
    
    animationRef.current = requestAnimationFrame(simulateForces);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [processedData, dimensions, dragNode, render]);
  
  function getNodeColor(role: string): string {
    switch (role?.toLowerCase()) {
      case 'main':
        return '#ff6b6b';
      case 'supporting':
        return '#4ecdc4';
      case 'minor':
        return '#ffd166';
      default:
        return '#6a89cc';
    }
  }

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full min-h-[600px] relative border rounded-lg bg-white/5"
      style={{ position: 'relative' }}
    >
      <canvas 
        ref={canvasRef} 
        width={dimensions.width} 
        height={dimensions.height}
        className="w-full h-full cursor-grab"
        style={{ cursor: isPanning ? 'grabbing' : (isDragging ? 'grabbing' : 'grab') }}
      />
      
      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-2">
        <button 
          className="w-8 h-8 bg-gray-800/80 hover:bg-gray-700 text-white rounded flex items-center justify-center"
          onClick={() => setTransform(prev => ({ ...prev, scale: Math.min(prev.scale * 1.2, 10) }))}
          title="Zoom in"
        >
          +
        </button>
        <button 
          className="w-8 h-8 bg-gray-800/80 hover:bg-gray-700 text-white rounded flex items-center justify-center"
          onClick={() => setTransform(prev => ({ ...prev, scale: Math.max(prev.scale / 1.2, 0.1) }))}
          title="Zoom out"
        >
          −
        </button>
        <button 
          className="w-8 h-8 bg-gray-800/80 hover:bg-gray-700 text-white rounded flex items-center justify-center text-xs"
          onClick={() => setTransform({ scale: 1, translateX: 0, translateY: 0 })}
          title="Reset view"
        >
          R
        </button>
      </div>
      
      {/* Instructions */}
      <div className="absolute top-2 right-2 bg-black/50 text-white text-xs p-1 rounded">
        <div>Scroll to zoom | Alt+drag to pan | R to reset</div>
      </div>
      
      {/* Debug information */}
      <div className="absolute top-2 left-2 bg-black/50 text-white text-xs p-1 rounded">
        Nodes: {processedData?.nodes.length || 0} | 
        Links: {processedData?.links.length || 0} | 
        Zoom: {Math.round(transform.scale * 100)}%
      </div>
      
      {/* Node tooltip */}
      {tooltipNode && (
        <div 
          className="absolute bg-black/80 text-white p-2 rounded shadow-lg z-10"
          style={{
            left: tooltipNode.x,
            top: tooltipNode.y - 10,
            transform: 'translate(-50%, -100%)'
          }}
        >
          <div className="font-bold">{tooltipNode.node.id}</div>
          <div className="text-xs">Role: {tooltipNode.node.role}</div>
          {tooltipNode.node.description && (
            <div className="text-xs mt-1">{tooltipNode.node.description}</div>
          )}
        </div>
      )}
      
      {/* Link tooltip */}
      {tooltipLink && (
        <div 
          className="absolute bg-black/80 text-white p-2 rounded shadow-lg z-10"
          style={{
            left: tooltipLink.x,
            top: tooltipLink.y - 10,
            transform: 'translate(-50%, -100%)'
          }}
        >
          <div className="text-xs">{tooltipLink.source} → {tooltipLink.target}</div>
          <div className="text-xs font-bold">{tooltipLink.type}</div>
        </div>
      )}
    </div>
  );
};

export default CharacterGraph;