import { useEffect, useCallback } from 'react';
import { useStore } from '@/store/useStore';
import api from '@/services/api';
import ws from '@/services/websocket';
import type { TradingSignal } from '@/types';

export function useSignals() {
  const {
    signals,
    selectedCurrencyPair,
    selectedTimeWindow,
    signalFilter,
    setSignals,
    addSignal,
    setSelectedCurrencyPair,
    setSelectedTimeWindow,
    setSignalFilter,
    isLoading,
    setLoading,
    error,
    setError,
  } = useStore();

  const fetchSignals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLatestSignals(
        signalFilter === 'all' ? undefined : [selectedCurrencyPair],
        selectedTimeWindow
      );
      setSignals(data);
    } catch (err) {
      setError('Failed to fetch signals');
      console.error('Error fetching signals:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedCurrencyPair, selectedTimeWindow, signalFilter, setSignals, setLoading, setError]);

  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);

  useEffect(() => {
    ws.connect();
    ws.subscribe({ signals: true });

    const handler = (signal: TradingSignal) => {
      if (signalFilter === 'all' || signal.currency_pair === selectedCurrencyPair) {
        addSignal(signal);
      }
    };

    ws.on('signal', handler);

    return () => {
      ws.off('signal', handler);
    };
  }, [addSignal, selectedCurrencyPair, signalFilter]);

  return {
    signals,
    selectedCurrencyPair,
    selectedTimeWindow,
    signalFilter,
    setSelectedCurrencyPair,
    setSelectedTimeWindow,
    setSignalFilter,
    isLoading,
    error,
    refreshSignals: fetchSignals,
  };
}
