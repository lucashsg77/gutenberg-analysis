export interface BookHistoryItem {
  id: string;
  title: string;
  timestamp: number;
}

const HISTORY_KEY = 'gutenberg-book-history';
const MAX_HISTORY_ITEMS = 20;

export function saveBookToHistory(bookId: string, bookTitle?: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    const existingHistory = localStorage.getItem(HISTORY_KEY);
    let historyItems: BookHistoryItem[] = [];
    
    if (existingHistory) {
      historyItems = JSON.parse(existingHistory);
    }

    historyItems = historyItems.filter(item => item.id !== bookId);

    historyItems.unshift({
      id: bookId,
      title: bookTitle || `Book #${bookId}`,
      timestamp: Date.now()
    });

    if (historyItems.length > MAX_HISTORY_ITEMS) {
      historyItems = historyItems.slice(0, MAX_HISTORY_ITEMS);
    }

    localStorage.setItem(HISTORY_KEY, JSON.stringify(historyItems));
  } catch (error) {
    console.error('Failed to save book to history:', error);
  }
}

export function getBookHistory(): BookHistoryItem[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const historyString = localStorage.getItem(HISTORY_KEY);
    if (!historyString) return [];
    
    return JSON.parse(historyString);
  } catch (error) {
    console.error('Failed to retrieve book history:', error);
    return [];
  }
}

export function clearBookHistory(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch (error) {
    console.error('Failed to clear book history:', error);
  }
}