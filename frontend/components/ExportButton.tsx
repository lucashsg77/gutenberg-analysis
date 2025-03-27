import React from 'react';
import { Button } from '@/components/ui';
import { BookData, AnalysisData } from '@/types';

interface ExportButtonProps {
  bookData: BookData;
  analysisData: AnalysisData;
}

const ExportButton: React.FC<ExportButtonProps> = ({ bookData, analysisData }) => {
  const handleExport = () => {
    const exportData = {
      book: {
        id: bookData.metadata.id,
        title: bookData.metadata.title,
        author: bookData.metadata.author,
        exportedAt: new Date().toISOString(),
      },
      characters: analysisData.characters.map(char => ({
        name: char.name,
        role: char.role,
        description: char.description,
        ...(char.aliases && { aliases: char.aliases }),
      })),
      relationships: analysisData.graph.links.map(link => ({
        source: link.source,
        target: link.target,
        type: link.type,
        value: link.value,
      })),
      themes: analysisData.themes,
      sentiment: analysisData.sentiment,
      key_quotes: analysisData.key_quotes,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${bookData.metadata.id}-${bookData.metadata.title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-analysis.json`;
    document.body.appendChild(a);
    a.click();

    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Button
      onClick={handleExport}
      variant="outline"
      size="sm"
      className="flex items-center gap-2"
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        width="16" 
        height="16" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Export Analysis
    </Button>
  );
};

export default ExportButton;