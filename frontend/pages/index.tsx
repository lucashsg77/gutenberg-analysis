import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import { 
  Button, 
  Input, 
  Label,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  Alert,
  AlertTitle,
  AlertDescription
} from '@/components/ui';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import LoadingState from '@/components/LoadingState';
import BookFetchingState from '@/components/BookFetchingState';
import BookAnalysis from '@/components/BookAnalysis';
import BookHistory from '@/components/BookHistory';
import { 
  fetchBook, 
  startAnalysis, 
  getAnalysisResults,
  getBookContent,
  BookFetchEventStream
} from '@/utils/api';
import { AnalysisEventStream } from '@/utils/eventStream';
import { BookData, AnalysisData, AnalysisStatus, BookFetchStatus } from '@/types';
import { saveBookToHistory } from '@/utils/bookHistory';

export default function Home() {
  const [bookId, setBookId] = useState<string>('1787');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [bookData, setBookData] = useState<BookData | null>(null);
  const [bookFetchStatus, setBookFetchStatus] = useState<BookFetchStatus | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const bookFetchStreamRef = useRef<BookFetchEventStream | null>(null);
  const bookFetchUnsubscribeRef = useRef<(() => void) | null>(null);
  const analysisStreamRef = useRef<AnalysisEventStream | null>(null);
  const analysisUnsubscribeRef = useRef<(() => void) | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBookId(e.target.value);
  };

  const cleanupBookFetchStream = () => {
    if (bookFetchUnsubscribeRef.current) {
      console.log('Unsubscribing from book fetch stream');
      bookFetchUnsubscribeRef.current();
      bookFetchUnsubscribeRef.current = null;
    }
    
    if (bookFetchStreamRef.current) {
      console.log('Disconnecting book fetch stream');
      bookFetchStreamRef.current.disconnect();
      bookFetchStreamRef.current = null;
    }
  };
  
  const cleanupAnalysisStream = () => {
    if (analysisUnsubscribeRef.current) {
      console.log('Unsubscribing from analysis stream');
      analysisUnsubscribeRef.current();
      analysisUnsubscribeRef.current = null;
    }
    
    if (analysisStreamRef.current) {
      console.log('Disconnecting analysis stream');
      analysisStreamRef.current.disconnect();
      analysisStreamRef.current = null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!bookId.trim()) {
      setError('Please enter a valid Project Gutenberg book ID');
      return;
    }

    setLoading(true);
    setError(null);
    setBookData(null);
    setBookFetchStatus(null);
    setAnalysisStatus(null);
    setAnalysisData(null);
    
    cleanupBookFetchStream();
    cleanupAnalysisStream();
    
    try {
      console.log(`Starting book fetch with ID: ${bookId}`);
      
      const fetchResponse = await fetchBook(bookId);
      console.log('Fetch response:', fetchResponse);
      
      if (fetchResponse.status === 'complete') {
        console.log('Book is already available, getting content');
        try {
          const book = await getBookContent(bookId);
          setBookData(book);
          console.log('Book data fetched successfully');
          
          // Save to history after successful fetch
          saveBookToHistory(bookId, book.metadata?.title);
          
          await startBookAnalysis(bookId);
        } catch (error) {
          console.error('Error getting book content:', error);
          const errorMessage = error instanceof Error ? error.message : 'An error occurred';
          setError(errorMessage);
        }
      } else if (fetchResponse.status === 'processing') {
        console.log('Book fetch is in progress, setting up SSE');
        setupBookFetchStream(bookId);
      } else if (fetchResponse.status === 'error') {
        throw new Error(fetchResponse.message || 'Failed to fetch book');
      }
    } catch (error) {
      console.error('Error during form submission:', error);
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const setupBookFetchStream = (bookId: string) => {
    console.log(`Setting up book fetch stream for ID: ${bookId}`);
    
    const eventStream = new BookFetchEventStream(bookId);
    bookFetchStreamRef.current = eventStream;
    
    const unsubscribe = eventStream.subscribe((status) => {
      console.log('Book fetch status update:', status);
      
      setBookFetchStatus(status);
      
      if (status.status === 'complete') {
        console.log('Book fetch complete, getting content');
        getBookContent(bookId)
          .then(book => {
            setBookData(book);
            console.log('Book data fetched successfully');
            
            // Save to history after successful fetch
            saveBookToHistory(bookId, book.metadata?.title);

            setBookFetchStatus(null);
            
            startBookAnalysis(bookId);
          })
          .catch(error => {
            console.error('Error getting book content:', error);
            const errorMessage = error instanceof Error ? error.message : 'An error occurred';
            setError(errorMessage);
          })
          .finally(() => {
            cleanupBookFetchStream();
          });
      }
      
      if (status.status === 'error') {
        console.error('Book fetch error:', status.message);
        setError(status.message || 'Book fetch failed');
        
        cleanupBookFetchStream();
      }
    });
    
    bookFetchUnsubscribeRef.current = unsubscribe;
  };
  
  const startBookAnalysis = async (bookId: string) => {
    try {
      console.log('Starting analysis...');
      const status = await startAnalysis(bookId);
      console.log(`Initial analysis status: ${status.status}`);
      setAnalysisStatus(status);

      if (status.status === 'complete') {
        console.log('Analysis already complete, fetching results');
        const results = await getAnalysisResults(bookId);
        setAnalysisData(results);
      } else if (status.status === 'processing') {
        setupAnalysisStream(bookId);
      } else if (status.status === 'error') {
        throw new Error(status.message || 'Analysis failed');
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setError(errorMessage);
    }
  };

  const setupAnalysisStream = (bookId: string) => {
    console.log(`Setting up analysis stream for book ID: ${bookId}`);
    
    const eventStream = new AnalysisEventStream(bookId);
    analysisStreamRef.current = eventStream;
    
    const unsubscribe = eventStream.subscribe((status) => {
      console.log('Analysis status update:', status);
      
      setAnalysisStatus(status);
      
      if (status.status === 'complete') {
        console.log('Analysis complete via event stream, fetching results');
        getAnalysisResults(bookId)
          .then(results => {
            setAnalysisData(results);
            console.log('Analysis results fetched successfully');
          })
          .catch(error => {
            console.error('Error fetching results:', error);
            if (error instanceof Error && !error.message.includes('still in progress')) {
              setError(`Error fetching results: ${error.message}`);
            }
          })
          .finally(() => {
            cleanupAnalysisStream();
          });
      }
      
      if (status.status === 'error') {
        console.error('Analysis error:', status.message);
        setError(status.message || 'Analysis failed');
        
        cleanupAnalysisStream();
      }
    });
    
    analysisUnsubscribeRef.current = unsubscribe;
  };

  useEffect(() => {
    return () => {
      cleanupBookFetchStream();
      cleanupAnalysisStream();
    };
  }, []);

  const isProcessing = loading || 
    (bookFetchStatus?.status === 'processing') || 
    (analysisStatus?.status === 'processing');

  return (
    <>
      <Head>
        <title>Gutenberg Book Analysis</title>
        <meta name="description" content="Analyze books from Project Gutenberg using LLM" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex flex-col min-h-screen">
        <NavBar />
        
        <main className="flex-grow container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold mb-4">Gutenberg Book Analysis</h1>
              <p className="text-xl text-muted-foreground">
                Analyze books from Project Gutenberg with an AI-powered character network visualization
              </p>
            </div>

            {/* Recently analyzed books history */}
            <BookHistory 
              onSelect={setBookId} 
              disabled={isProcessing}
            />

            {/* Book ID form */}
            <Card className="mb-10">
              <CardHeader>
                <CardTitle>Enter a Book ID</CardTitle>
                <CardDescription>
                  Enter a Project Gutenberg book ID to analyze. For example, Hamlet is 1787.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                    <div className="flex flex-col space-y-1.5 md:col-span-3">
                      <Label htmlFor="bookId">Project Gutenberg Book ID</Label>
                      <Input
                        id="bookId"
                        placeholder="Enter book ID (e.g., 1787)"
                        value={bookId}
                        onChange={handleInputChange}
                        disabled={isProcessing}
                      />
                    </div>
                    <div className="flex items-end md:col-span-1">
                      <Button 
                        type="submit" 
                        className="w-full"
                        disabled={isProcessing}
                      >
                        {loading ? 'Loading...' : 'Analyze Book'}
                      </Button>
                    </div>
                  </div>
                </form>

                <div className="mt-4">
                  <h3 className="text-sm font-medium mb-2">Some popular book IDs to try:</h3>
                  <div className="flex flex-wrap gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setBookId('1342')}
                      disabled={isProcessing}
                    >
                      1342 - Pride and Prejudice
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setBookId('84')}
                      disabled={isProcessing}
                    >
                      84 - Frankenstein
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setBookId('1661')}
                      disabled={isProcessing}
                    >
                      1661 - Sherlock Holmes
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setBookId('11')}
                      disabled={isProcessing}
                    >
                      11 - Alice in Wonderland
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setBookId('2701')}
                      disabled={isProcessing}
                    >
                      2701 - Moby Dick
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Connection debug information */}
            {(bookFetchStatus?.status === 'processing' || analysisStatus?.status === 'processing') && (
              <div className="mb-2 text-xs text-gray-500">
                <p>Real-time connection: {process.env.NEXT_PUBLIC_API_URL}</p>
                {bookFetchStatus?.status === 'processing' && (
                  <p>Book fetch stage: {bookFetchStatus.stage || 'processing'}</p>
                )}
                {analysisStatus?.status === 'processing' && (
                  <p>Analysis stage: {analysisStatus.stage || 'processing'}</p>
                )}
              </div>
            )}

            {/* Error message */}
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Book fetching state */}
            {bookFetchStatus && bookFetchStatus.status === 'processing' && (
              <BookFetchingState 
                status={bookFetchStatus} 
                bookId={bookId}
              />
            )}

            {/* Analysis loading state */}
            {analysisStatus && analysisStatus.status === 'processing' && !bookFetchStatus && (
              <LoadingState 
                status={analysisStatus} 
                bookId={bookId}
                bookTitle={bookData?.metadata?.title}
              />
            )}

            {/* Analysis results */}
            {bookData && analysisData && (
              <BookAnalysis bookData={bookData} analysisData={analysisData} />
            )}
          </div>
        </main>

        <Footer />
      </div>
    </>
  );
}