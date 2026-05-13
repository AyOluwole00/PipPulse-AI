import { create } from 'zustand';
import type {
  TradingSignal,
  NewsItemResponse,
  SystemConfig,
  SystemStats,
  SignalDirection,
  TimeWindow,
} from '@/types';

interface StoreState {
  // Signals
  signals: TradingSignal[];
  selectedCurrencyPair: string;
  selectedTimeWindow: TimeWindow;
  setSignals: (signals: TradingSignal[]) => void;
  addSignal: (signal: TradingSignal) => void;
  setSelectedCurrencyPair: (pair: string) => void;
  setSelectedTimeWindow: (window: TimeWindow) => void;

  // News
  news: NewsItemResponse[];
  setNews: (news: NewsItemResponse[]) => void;
  addNewsItem: (item: NewsItemResponse) => void;

  // Config
  config: SystemConfig | null;
  setConfig: (config: SystemConfig) => void;

  // Stats
  stats: SystemStats | null;
  setStats: (stats: SystemStats) => void;

  // UI State
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // WebSocket
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;

  // Filters
  signalFilter: SignalDirection | 'all';
  setSignalFilter: (filter: SignalDirection | 'all') => void;
}

export const useStore = create<StoreState>((set) => ({
  // Signals
  signals: [],
  selectedCurrencyPair: 'EUR/USD',
  selectedTimeWindow: '1hour',
  setSignals: (signals) => set({ signals }),
  addSignal: (signal) => set((state) => ({
    signals: [signal, ...state.signals].slice(0, 100), // Keep last 100 signals
  })),
  setSelectedCurrencyPair: (pair) => set({ selectedCurrencyPair: pair }),
  setSelectedTimeWindow: (window) => set({ selectedTimeWindow: window }),

  // News
  news: [],
  setNews: (news) => set({ news }),
  addNewsItem: (item) => set((state) => ({
    news: [item, ...state.news].slice(0, 50), // Keep last 50 news items
  })),

  // Config
  config: null,
  setConfig: (config) => set({ config }),

  // Stats
  stats: null,
  setStats: (stats) => set({ stats }),

  // UI State
  isLoading: false,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  // WebSocket
  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),

  // Filters
  signalFilter: 'all',
  setSignalFilter: (filter) => set({ signalFilter: filter }),
}));
