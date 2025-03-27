import React, { useState } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  CardDescription,
  Alert,
  AlertTitle,
  AlertDescription,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from '@/components/ui';
import CharacterGraph from './CharacterGraph';
import ExportButton from './ExportButton';
import { BookData, AnalysisData, Theme, Quote } from '@/types';
import Image from 'next/image';

interface BookAnalysisProps {
  bookData: BookData;
  analysisData: AnalysisData;
}

const BookAnalysis: React.FC<BookAnalysisProps> = ({ bookData, analysisData }) => {
  const [activeTab, setActiveTab] = useState('graph');
  const { metadata } = bookData;
  
  return (
    <div className="space-y-8">
      {/* Book header */}
      <Card className="border-2 border-primary/20">
        <CardHeader className="pb-2">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Book cover */}
            <div className="flex-shrink-0">
              <div className="relative w-32 h-48 overflow-hidden rounded-md border shadow-md">
                <Image 
                  src={metadata.cover_url || '/placeholder-cover.jpg'} 
                  alt={metadata.title}
                  fill
                  sizes="(max-width: 768px) 100vw, 128px"
                  style={{ objectFit: 'cover' }}
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.onerror = null;
                    target.src = '/placeholder-cover.jpg';
                  }}
                />
              </div>
            </div>
            
            {/* Book info */}
            <div className="flex-grow">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl md:text-3xl mb-2">{metadata.title}</CardTitle>
                  <CardDescription className="text-lg">by {metadata.author}</CardDescription>
                </div>
                <ExportButton bookData={bookData} analysisData={analysisData} />
              </div>
              
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                <div>
                  <span className="font-semibold">Language:</span> {metadata.language}
                </div>
                <div>
                  <span className="font-semibold">Released:</span> {metadata.release_date}
                </div>
                <div>
                  <span className="font-semibold">Downloads:</span> {metadata.downloads.toLocaleString()}
                </div>
                <div>
                  <span className="font-semibold">Book ID:</span> {metadata.id}
                </div>
              </div>
              
              {/* Subjects/Tags */}
              {metadata.subject && metadata.subject.length > 0 && (
                <div className="mt-4">
                  <div className="font-semibold mb-1">Subjects:</div>
                  <div className="flex flex-wrap gap-2">
                    {metadata.subject.map((subject, index) => (
                      <span key={index} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                        {subject}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>
      
      {/* Analysis tabs */}
      <Tabs defaultValue="graph">
        <TabsList className="w-full flex justify-start mb-6 border-b">
          <TabsTrigger 
            value="graph" 
            active={activeTab === 'graph'}
            onClick={() => setActiveTab('graph')}
          >
            Character Network
          </TabsTrigger>
          <TabsTrigger 
            value="themes" 
            active={activeTab === 'themes'}
            onClick={() => setActiveTab('themes')}
          >
            Themes & Sentiment
          </TabsTrigger>
          <TabsTrigger 
            value="quotes" 
            active={activeTab === 'quotes'}
            onClick={() => setActiveTab('quotes')}
          >
            Key Quotes
          </TabsTrigger>
          <TabsTrigger 
            value="characters" 
            active={activeTab === 'characters'}
            onClick={() => setActiveTab('characters')}
          >
            Character Details
          </TabsTrigger>
        </TabsList>
        
        {/* Character Network Graph */}
        <TabsContent value="graph" active={activeTab === 'graph'}>
          <div className="space-y-4">
            <Alert>
              <AlertTitle>Character Network Visualization</AlertTitle>
              <AlertDescription>
                This network graph shows relationships between characters in the book. 
                Hover over nodes and connections to see more details.
                <ul className="mt-2 list-disc list-inside">
                  <li>Node size represents character importance</li>
                  <li>Line thickness represents relationship strength</li>
                  <li>Colors indicate character role: Red (Main), Teal (Supporting), Yellow (Minor)</li>
                </ul>
              </AlertDescription>
            </Alert>
            
            <Card className="overflow-hidden">
              <CardContent className="p-0 h-[600px]">
                <CharacterGraph graphData={analysisData.graph} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        {/* Themes & Sentiment */}
        <TabsContent value="themes" active={activeTab === 'themes'}>
          <div className="grid grid-cols-1 gap-6">
            {/* Sentiment Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Sentiment Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="text-lg font-semibold mb-1">Overall Sentiment: 
                    <span className={`ml-2 ${getSentimentColor(analysisData.sentiment.overall)}`}>
                      {analysisData.sentiment.overall?.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">{analysisData.sentiment.analysis}</p>
                </div>
              </CardContent>
            </Card>
            
            {/* Themes */}
            <Card>
              <CardHeader>
                <CardTitle>Key Themes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {analysisData.themes.map((theme) => (
                    <ThemeCard key={theme.name} theme={theme} />
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        {/* Key Quotes */}
        <TabsContent value="quotes" active={activeTab === 'quotes'}>
          <Card>
            <CardHeader>
              <CardTitle>Significant Quotes</CardTitle>
              <CardDescription>
                Key passages that highlight important moments or themes in the text
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {analysisData.key_quotes.map((quote) => (
                  <QuoteCard key={quote.quote} quote={quote} />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Character Details */}
        <TabsContent value="characters" active={activeTab === 'characters'}>
          <Card>
            <CardHeader>
              <CardTitle>Character Details</CardTitle>
              <CardDescription>
                Information about each character identified in the text
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
                {analysisData.characters.map((character, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <h3 className="text-xl font-semibold mb-2 border-b pb-2">{character.name}</h3>
                    
                    <div className="mb-2 flex items-center">
                      <span className={`inline-block px-2 py-1 text-xs rounded-full ${getRoleBadgeColor(character.role)}`}>
                        {character.role}
                      </span>
                      
                      {character.aliases && character.aliases.length > 0 && (
                        <span className="text-xs text-muted-foreground ml-3">
                          Also known as: {character.aliases.join(', ')}
                        </span>
                      )}
                    </div>
                    
                    <p className="mb-3 text-muted-foreground text-sm">{character.description}</p>
                    
                    {character.relationships && character.relationships.length > 0 && (
                      <>
                        <h4 className="font-medium mb-2 text-sm">Relationships:</h4>
                        <ul className="space-y-1">
                          {character.relationships.map((rel, idx) => (
                            <li key={idx} className="text-xs flex items-center">
                              <div className="w-2 h-2 rounded-full bg-primary/60 mr-2"></div>
                              <span className="font-medium">{rel.character}:</span> 
                              <span className="ml-1">{rel.type}</span>
                              {rel.strength && (
                                <span className="ml-1 text-muted-foreground">
                                  (Strength: {rel.strength}/10)
                                </span>
                              )}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ThemeCard: React.FC<{ theme: Theme }> = ({ theme }) => (
  <div className="border-l-4 border-primary/70 pl-4 py-1">
    <h3 className="text-lg font-medium mb-1">{theme.name}</h3>
    <p className="text-muted-foreground">{theme.description}</p>
  </div>
);

const QuoteCard: React.FC<{ quote: Quote }> = ({ quote }) => (
  <div className="border-l-4 border-secondary pl-4 py-2">
    <blockquote className="text-lg italic mb-2">{quote.quote}</blockquote>
    
    {quote.speaker && (
      <div className="text-primary font-medium">— {quote.speaker}</div>
    )}
    
    <div className="mt-2 text-sm">
      <div className="mb-1"><span className="font-medium">Context:</span> {quote.context}</div>
      <div><span className="font-medium">Significance:</span> {quote.significance}</div>
    </div>
  </div>
);

function getSentimentColor(sentiment: string): string {
  switch (sentiment?.toLowerCase()) {
    case 'positive':
      return 'text-green-500';
    case 'negative':
      return 'text-red-500';
    case 'mixed':
      return 'text-yellow-500';
    default:
      return 'text-blue-500';
  }
}

function getRoleBadgeColor(role: string): string {
  switch (role?.toLowerCase()) {
    case 'main':
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
    case 'supporting':
      return 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-200';
    case 'minor':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
    default:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
  }
}

export default BookAnalysis;