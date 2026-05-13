import { useEffect, useCallback } from 'react';
import { useStore } from '@/store/useStore';
import api from '@/services/api';
import ws from '@/services/websocket';
import type { NewsItemResponse } from '@/types';

export function useNews(limit = 20) {
  const {
    news,
    setNews,
    addNewsItem,
    isLoading,
    setLoading,
    error,
    setError,
  } = useStore();

  const fetchNews = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLatestNews(limit);
      setNews(data.items || []);
    } catch (err) {
      setError('Failed to fetch news');
      console.error('Error fetching news:', err);
    } finally {
      setLoading(false);
    }
  }, [limit, setNews, setLoading, setError]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  useEffect(() => {
    // Subscribe to news updates
    ws.on('news', (item: NewsItemResponse) => {
      addNewsItem(item);
    });

    return () => {
      ws.off('news', addNewsItem);
    };
  }, [addNewsItem]);

  return {
    news,
    isLoading,
    error,
    refreshNews: fetchNews,
  };
}
