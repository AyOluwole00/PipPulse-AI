export type SourceType = 'newsapi' | 'twitter' | 'reddit' | 'telegram';

export type SentimentLabel = 'positive' | 'negative' | 'neutral';

export type SignalDirection = 'buy' | 'sell' | 'hold';

export type TimeWindow = '15min' | '1hour' | '4hour';

export interface RawNewsItem {
  source: SourceType;
  source_id: string;
  content: string;
  title?: string;
  author?: string;
  url?: string;
  timestamp: string;
  currency_pairs: string[];
  metadata: Record<string, any>;
  content_hash?: string;
}

export interface ProcessedNewsItem extends RawNewsItem {
  cleaned_content: string;
  language: string;
  is_spam: boolean;
  is_bot: boolean;
}

export interface SentimentResult {
  content_hash: string;
  label: SentimentLabel;
  confidence: number;
  probabilities: Record<string, number>;
  timestamp: string;
  model_name: string;
  pair_sentiment: Record<string, number>;
}

export interface TradingSignal {
  currency_pair: string;
  direction: SignalDirection;
  strength: number;
  confidence: number;
  timestamp: string;
  time_window: TimeWindow;
  reference_price?: number;
  supporting_headlines: string[];
  reasoning: string;
  sentiment_score: number;
  volume: number;
  consensus_factor: number;
}

export interface SignalResponse {
  currency_pair: string;
  direction: SignalDirection;
  strength: number;
  confidence: number;
  timestamp: string;
  time_window: TimeWindow;
  reasoning: string;
  supporting_headlines: string[];
}

export interface SentimentTrend {
  currency_pair: string;
  timestamps: string[];
  sentiment_scores: number[];
  signal_counts: number[];
}

export interface NewsItemResponse {
  source: SourceType;
  title?: string;
  content: string;
  url?: string;
  timestamp: string;
  currency_pairs: string[];
  sentiment?: SentimentResult;
}

export interface BacktestResult {
  currency_pair: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  win_rate: number;
  average_risk_reward: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  confidence_calibration: Record<string, number>;
}

export interface SystemConfig {
  signal: {
    latency_target: number;
    max_batch_size: number;
    confidence_threshold: number;
    time_decay_lambda: number;
  };
  source_weights: Record<string, number>;
  time_windows: Record<string, number>;
  currency_pairs: string[];
  model: {
    name: string;
    cache_dir: string;
  };
}

export interface ThresholdConfig {
  currency_pair: string;
  buy_threshold: number;
  sell_threshold: number;
  confidence_threshold: number;
  time_decay_lambda: number;
}

export interface WebSocketMessage {
  type: 'signal' | 'news' | 'error' | 'heartbeat' | 'connected' | 'subscribed';
  data?: any;
  timestamp: string;
}

export interface SystemStats {
  news: {
    total_count: number;
    last_update?: string;
  };
  signals: {
    total_count: number;
    last_update?: string;
  };
  timestamp: string;
}
