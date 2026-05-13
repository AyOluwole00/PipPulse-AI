'use client';

import { ExternalLink, Clock, Newspaper } from 'lucide-react';
import type { NewsItemResponse } from '@/types';

interface NewsFeedProps {
  news: NewsItemResponse[];
  isLoading?: boolean;
}

export function NewsFeed({ news, isLoading }: NewsFeedProps) {
  const getSentimentColor = (label?: string) => {
    switch (label) {
      case 'positive':
        return 'bg-success-100 text-success-700';
      case 'negative':
        return 'bg-danger-100 text-danger-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'newsapi':
        return 'News API';
      case 'twitter':
        return 'Twitter/X';
      case 'reddit':
        return 'Reddit';
      case 'telegram':
        return 'Telegram';
      default:
        return source;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <Newspaper className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">No news available</p>
        <p className="text-sm">Check back later for updates</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {news.map((item, index) => (
        <article
          key={`${item.source}-${item.timestamp}-${index}`}
          className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500 uppercase">
                {getSourceLabel(item.source)}
              </span>
              {item.sentiment && (
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(item.sentiment.label)}`}
                >
                  {item.sentiment.label}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>{formatTime(item.timestamp)}</span>
            </div>
          </div>

          {item.title && (
            <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
              {item.title}
            </h3>
          )}

          <p className="text-gray-600 text-sm mb-3 line-clamp-3">
            {item.content}
          </p>

          <div className="flex items-center justify-between">
            {item.currency_pairs && item.currency_pairs.length > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">Pairs:</span>
                {item.currency_pairs.slice(0, 3).map((pair) => (
                  <span
                    key={pair}
                    className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium text-gray-700"
                  >
                    {pair}
                  </span>
                ))}
                {item.currency_pairs.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{item.currency_pairs.length - 3}
                  </span>
                )}
              </div>
            )}

            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
              >
                Read more
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
