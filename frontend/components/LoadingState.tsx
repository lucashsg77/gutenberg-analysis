import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Progress } from '@/components/ui';
import { AnalysisStatus } from '@/types';

interface LoadingStateProps {
  status: AnalysisStatus;
  bookId: string;
  bookTitle?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({ status, bookId, bookTitle }) => {
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [processingStage, setProcessingStage] = useState<string>('');
  const [factIndex, setFactIndex] = useState<number>(0);
  const progress = status.progress || 0;
  const message = status.message || 'Processing...';
  const stage = status.stage || '';

  const didYouKnowFacts = [
    "This analysis extracts character relationships by analyzing dialogue patterns and narrative descriptions.",
    "The Brothers Karamazov by Dostoevsky contains over 160 named characters, making it one of the most character-dense novels in classic literature.",
    "Alice in Wonderland features 22 main characters, yet Lewis Carroll wrote it in just two days during a boat trip with the real Alice.",
    "Large Language Models can identify character archetypes by analyzing their actions, speech patterns, and relationships with others.",
    "In Shakespeare's plays, there are over 1,200 total characters, with Hamlet having the most speaking parts of any single play."
  ];

  const funFacts = [
    "Some classic literature contains over 100 named characters, with complex relationship networks spanning entire families.",
    "War and Peace by Tolstoy features 559 characters, with about 200 of them being historical figures including Napoleon Bonaparte.",
    "Charles Dickens often named characters based on their personalities - like Mr. Murdstone (murder + stone) in David Copperfield being hard-hearted and cruel.",
    "The wizarding world of Harry Potter contains over 700 named characters across the seven books, with 167 appearing in the first book alone.",
    "Leo Tolstoy originally intended for Anna Karenina to be physically unattractive but changed his mind as he fell in love with her character during writing."
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const factRotator = setInterval(() => {
      setFactIndex(prev => (prev + 1) % Math.max(didYouKnowFacts.length, funFacts.length));
    }, 8000);
    
    return () => clearInterval(factRotator);
  }, [didYouKnowFacts.length, funFacts.length]);

  useEffect(() => {
    const estimatedTotal = progress > 0 ? (elapsedTime / progress) * 100 : 180;
    const remaining = Math.max(0, estimatedTotal - elapsedTime);
    setEstimatedTime(remaining);

    if (stage) {
      const stageMap: Record<string, string> = {
        'initialization': 'Initializing analysis',
        'text_processing': 'Processing text structure',
        'character_analysis_prep': 'Preparing character analysis',
        'character_analysis_in_progress': 'Identifying characters',
        'character_analysis_complete': 'Characters identified',
        'graph_generation_started': 'Starting network generation',
        'graph_generation': 'Building character network',
        'theme_analysis_started': 'Starting theme analysis',
        'theme_analysis_in_progress': 'Extracting themes and sentiment',
        'theme_analysis_complete': 'Themes extracted',
        'theme_analysis_rate_limited': 'Waiting for API (rate limited)',
        'finalization': 'Finalizing results'
      };
      
      setProcessingStage(stageMap[stage] || stage);
    } else {
      if (progress < 25) {
        setProcessingStage('Processing text structure');
      } else if (progress < 50) {
        setProcessingStage('Identifying characters and relationships');
      } else if (progress < 75) {
        setProcessingStage('Extracting themes and sentiment');
      } else {
        setProcessingStage('Finalizing character network');
      }
    }
  }, [progress, elapsedTime, bookId, stage]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="w-full mb-8">
      <CardHeader>
        <CardTitle>Analysis in Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium">{message}</span>
              <span className="text-xs ml-2 text-muted-foreground">
                {bookTitle ? `"${bookTitle}"` : `Book #${bookId}`}
              </span>
            </div>
            <span className="text-sm font-medium">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} max={100} />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Current stage: {processingStage}</span>
            <span>Time remaining: ~{formatTime(estimatedTime)}</span>
          </div>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          <div className="text-sm text-muted-foreground max-w-xl">
            <p>
              LLM analysis is working on identifying characters, themes, and relationships, please wait!
            </p>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="text-xs border rounded p-2 bg-primary/5 h-24 flex flex-col justify-center transition-opacity duration-300">
                <span className="font-medium">Did you know?</span> {didYouKnowFacts[factIndex % didYouKnowFacts.length]}
              </div>
              <div className="text-xs border rounded p-2 bg-primary/5 h-24 flex flex-col justify-center transition-opacity duration-300">
                <span className="font-medium">Fun fact:</span> {funFacts[factIndex % funFacts.length]}
              </div>
            </div>
          </div>
        </div>
        
        {/* Elapsed time indicator */}
        <div className="text-xs text-right text-muted-foreground">
          Analysis time: {formatTime(elapsedTime)}
        </div>
      </CardContent>
    </Card>
  );
};

export default LoadingState;