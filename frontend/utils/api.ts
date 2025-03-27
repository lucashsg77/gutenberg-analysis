import axios from 'axios';
import { 
  BookData, 
  AnalysisData,
  AnalysisStatus 
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('API URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: false
});

api.interceptors.request.use(config => {
  console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`);
  return config;
});

api.interceptors.response.use(
  response => {
    console.log(`Received response from ${response.config.url}:`, response.status);
    return response;
  },
  error => {
    if (error.response) {
      console.error(`API error (${error.response.status}):`, error.response.data);
    } else if (error.request) {
      console.error('API request made but no response received:', error.message);
      if (error.code === 'ECONNABORTED') {
        console.error('Request timed out. Server might be overloaded.');
      } else {
        console.error('Connection issue. Backend might be down or CORS issue.');
      }
    } else {
      console.error('API request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export class BookFetchEventStream {
  private eventSource: EventSource | null = null;
  private bookId: string;
  private apiUrl: string;
  private callbacks: ((status: any) => void)[] = [];
  private connected: boolean = false;

  constructor(bookId: string) {
    this.bookId = bookId;
    this.apiUrl = API_URL;
  }

  public connect(): void {
    if (this.connected) return;

    try {
      const url = `${this.apiUrl}/api/fetch-stream/${this.bookId}`;
      console.log(`Connecting to book fetch stream at: ${url}`);
      
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = () => {
        console.log('Book fetch stream connected');
        this.connected = true;
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Book fetch stream update:', data);

          this.callbacks.forEach(callback => callback(data));

          if (data.status === 'complete' || data.status === 'error') {
            this.disconnect();
          }
        } catch (error) {
          console.error('Error parsing book fetch stream data:', error);
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.error('Book fetch stream error:', error);
        this.disconnect();
      };
    } catch (error) {
      console.error('Failed to connect to book fetch stream:', error);
    }
  }

  public disconnect(): void {
    if (this.eventSource) {
      console.log('Disconnecting from book fetch stream');
      this.eventSource.close();
      this.eventSource = null;
      this.connected = false;
    }
  }

  public subscribe(callback: (status: any) => void): () => void {
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

export const fetchBook = async (bookId: string): Promise<any> => {
  try {
    console.log(`Initiating book fetch with ID: ${bookId}`);
    const response = await api.post('/api/book', { book_id: bookId });
    console.log('Book fetch initiated:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in fetchBook:', error);
    if (axios.isAxiosError(error)) {
      if (error.message.includes('Network Error')) {
        console.error('Possible CORS issue or server unreachable');
        throw new Error('Cannot connect to API server. Please check if the server is running and CORS is configured correctly.');
      }
      if (error.response) {
        throw new Error(error.response.data.detail || `Failed to fetch book: ${error.message}`);
      }
    }
    throw new Error('Failed to fetch book. Please check your connection and try again.');
  }
};

export const getBookContent = async (bookId: string): Promise<BookData> => {
  try {
    console.log(`Getting book content for ID: ${bookId}`);
    const response = await api.get(`/api/book-content/${bookId}`);
    console.log('Book content received');
    return response.data;
  } catch (error) {
    console.error('Error in getBookContent:', error);
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 202) {
        throw new Error('Book fetch is still in progress');
      }
      if (error.response) {
        throw new Error(error.response.data.detail || `Failed to get book content: ${error.message}`);
      }
    }
    throw new Error('Failed to get book content. Please check your connection and try again.');
  }
};

export const startAnalysis = async (bookId: string): Promise<AnalysisStatus> => {
  try {
    const response = await api.post('/api/analyze', { book_id: bookId });
    console.log('Start analysis response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in startAnalysis:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || `Failed to start analysis: ${error.message}`);
    }
    throw new Error('Failed to start analysis. Please check your connection and try again.');
  }
};

export const getAnalysisStatus = async (bookId: string): Promise<AnalysisStatus> => {
  try {
    const response = await api.get(`/api/analysis-status/${bookId}`);
    console.log('Analysis status response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in getAnalysisStatus:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || `Failed to get analysis status: ${error.message}`);
    }
    throw new Error('Failed to get analysis status. Please check your connection and try again.');
  }
};

export const getAnalysisResults = async (bookId: string): Promise<AnalysisData> => {
  try {
    const response = await api.get(`/api/analysis/${bookId}`);
    console.log('Analysis results response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in getAnalysisResults:', error);
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 202) {
        console.log('Analysis still in progress (202 response)');
        throw new Error('Analysis is still in progress');
      }
      throw new Error(error.response.data.detail || `Failed to get analysis results: ${error.message}`);
    }
    throw new Error('Failed to get analysis results. Please check your connection and try again.');
  }
};