import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '@/components/ui';

interface BookHistoryItem {
  id: string;
  title: string;
  timestamp: number;
}

interface BookHistoryProps {
  onSelect: (bookId: string) => void;
  disabled: boolean;
}

const BookHistory: React.FC<BookHistoryProps> = ({ onSelect, disabled }) => {
  const [history, setHistory] = useState<BookHistoryItem[]>([]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    try {
      const storedHistory = localStorage.getItem('gutenberg-book-history');
      if (storedHistory) {
        const parsedHistory = JSON.parse(storedHistory);
        setHistory(parsedHistory);
      }
    } catch (error) {
      console.error('Failed to load book history:', error);
    }
  }, []);

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const clearHistory = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('gutenberg-book-history');
    }
    setHistory([]);
  };

  if (history.length === 0) {
    return null;
  }

  return (
    <Card className="mb-8">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle>Recent Books</CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={clearHistory}
            className="text-xs"
            disabled={disabled}
          >
            Clear
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {history.slice(0, 6).map((book) => (
            <Button
              key={`${book.id}-${book.timestamp}`}
              variant="outline"
              size="sm"
              className="justify-start text-left h-auto py-3"
              onClick={() => onSelect(book.id)}
              disabled={disabled}
            >
              <div className="flex flex-col items-start w-full overflow-hidden">
                <span className="font-medium truncate w-full block">
                  {book.title || `Book #${book.id}`}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatDate(book.timestamp)}
                </span>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default BookHistory;