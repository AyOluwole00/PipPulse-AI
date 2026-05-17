import { useEffect, useCallback } from 'react';
import { useStore } from '@/store/useStore';
import api from '@/services/api';
import ws from '@/services/websocket';
import type { NewsItemResponse } from '@/types';

export function useNews(currencyPair?: string, limit = 20, hours = 24) {
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
      const data = await api.getNews({
        currency_pair: currencyPair,
        limit,
        hours,
      });
      setNews(data || []);
    } catch (err) {
      setError('Failed to fetch news');
      console.error('Error fetching news:', err);
    } finally {
      setLoading(false);
    }
  }, [currencyPair, limit, hours, setNews, setLoading, setError]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  useEffect(() => {
    ws.connect();
    ws.subscribe({ news: true });

    const handler = (item: NewsItemResponse) => {
      if (!currencyPair || item.currency_pairs.includes(currencyPair)) {
        addNewsItem(item);
      }
    };

    ws.on('news', handler);

    return () => {
      ws.off('news', handler);
    };
  }, [addNewsItem, currencyPair]);

  return {
    news,
    isLoading,
    error,
    refreshNews: fetchNews,
  };
}
