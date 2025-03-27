import { AnalysisStatus } from '@/types';

type EventCallback = (status: AnalysisStatus) => void;

export class AnalysisEventStream {
  private eventSource: EventSource | null = null;
  private bookId: string;
  private apiUrl: string;
  private callbacks: EventCallback[] = [];
  private connected: boolean = false;

  constructor(bookId: string) {
    this.bookId = bookId;
    this.apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  public connect(): void {
    if (this.connected) return;

    try {
      const url = `${this.apiUrl}/api/analysis-stream/${this.bookId}`;
      console.log(`Connecting to event stream at: ${url}`);
      
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = () => {
        console.log('Event stream connected');
        this.connected = true;
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Event stream update:', data);

          this.callbacks.forEach(callback => callback(data));

          if (data.status === 'complete' || data.status === 'error') {
            this.disconnect();
          }
        } catch (error) {
          console.error('Error parsing event stream data:', error);
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.error('Event stream error:', error);
        this.disconnect();
      };
    } catch (error) {
      console.error('Failed to connect to event stream:', error);
    }
  }

  public disconnect(): void {
    if (this.eventSource) {
      console.log('Disconnecting from event stream');
      this.eventSource.close();
      this.eventSource = null;
      this.connected = false;
    }
  }

  public subscribe(callback: EventCallback): () => void {
    this.callbacks.push(callback);

    if (!this.connected) {
      this.connect();
    }

    return () => {
      this.callbacks = this.callbacks.filter(cb => cb !== callback);

      if (this.callbacks.length === 0) {
        this.disconnect();
      }
    };
  }
}
