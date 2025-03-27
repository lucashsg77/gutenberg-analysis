import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Progress } from '@/components/ui';

interface BookFetchStatus {
  status: 'processing' | 'complete' | 'error' | 'not_found';
  progress?: number;
  message?: string;
  stage?: string;
}

interface BookFetchingStateProps {
  status: BookFetchStatus;
  bookId: string;
}

const BookFetchingState: React.FC<BookFetchingStateProps> = ({ status }) => {
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const progress = status.progress || 5;
  const message = status.message || 'Fetching book...';
  const stage = status.stage || 'fetch_init';

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStageDescription = () => {
    switch(stage) {
      case 'fetch_init':
        return 'Initializing book fetch request. This typically takes a few seconds.';
      case 'metadata_fetch':
        return 'Fetching book metadata (title, author, etc.) from Project Gutenberg.';
      case 'content_fetch':
        return 'Downloading the full book content. This can take from 1 second to a few a minutes.';
      case 'content_cleaning':
        return 'Cleaning book content by removing headers and formatting text.';
      default:
        return 'Retrieving book from Project Gutenberg database.';
    }
  };

  const getStageIcon = () => {
    switch(stage) {
      case 'fetch_init':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
        );
      case 'metadata_fetch':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        );
      case 'content_fetch':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
        );
      case 'content_cleaning':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        );
    }
  };

  return (
    <Card className="w-full mb-8">
      <CardHeader>
        <CardTitle>Fetching Book</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{message}</span>
            <span className="text-sm font-medium">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} max={100} className="h-2" />
        </div>
        
        <div className="flex items-center space-x-4 bg-primary/5 p-4 rounded-md">
          <div className="animate-pulse w-10 h-10 rounded-full bg-primary/30 flex items-center justify-center text-primary">
            {getStageIcon()}
          </div>
          <div>
            <p className="text-sm">{getStageDescription()}</p>
          </div>
        </div>
        
        <div className="bg-amber-50 border-l-4 border-amber-400 p-3 text-xs text-amber-700">
          <p className="font-medium">Project Gutenberg Info:</p>
          <p>Project Gutenberg servers can sometimes be slow, especially for large books. Please be patient 
          while we fetch the complete text. Once cached, future analysis of this book will be much faster.</p>
        </div>
        
        {/* Elapsed time indicator */}
        <div className="text-xs text-right text-muted-foreground">
          Time elapsed: {formatTime(elapsedTime)}
        </div>
      </CardContent>
    </Card>
  );
};

export default BookFetchingState;