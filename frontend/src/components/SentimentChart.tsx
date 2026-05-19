'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { TradingSignal } from '@/types';

interface SentimentChartProps {
  signals: TradingSignal[];
  pair: string;
}

export function SentimentChart({ signals, pair }: SentimentChartProps) {
  const chartData = signals
    .filter((signal) => signal.currency_pair === pair)
    .map((signal) => ({
      time: new Date(signal.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      sentiment: signal.sentiment_score,
      volume: signal.volume,
    }))
    .sort((left, right) => left.time.localeCompare(right.time));

  if (chartData.length === 0) {
    return <div className="h-64 flex items-center justify-center text-slate-400">No sentiment data available for {pair}</div>;
  }

  const formatTime = (tickItem: string) => tickItem;

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tickFormatter={formatTime}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            domain={[-1, 1]}
            tickFormatter={(value) => value.toFixed(1)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />
          <ReferenceLine y={0.3} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
          <ReferenceLine y={-0.3} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Line
            type="monotone"
            dataKey="sentiment"
            stroke="#0ea5e9"
            strokeWidth={2}
            dot={{ fill: '#0ea5e9', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
