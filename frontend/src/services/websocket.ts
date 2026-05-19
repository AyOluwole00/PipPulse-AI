import type { WebSocketMessage } from '@/types';
import api from '@/services/api';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
const WS_ENDPOINT = WS_BASE.endsWith('/ws')
  ? WS_BASE
  : `${WS_BASE.replace(/\/$/, '')}/ws`;

type EventHandler = (data: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private connectPromise: Promise<void> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  async connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    if (this.connectPromise) {
      return this.connectPromise;
    }

    this.connectPromise = (async () => {
      const backendAvailable = await api.isBackendAvailable();

      if (!backendAvailable) {
        return;
      }

      if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
        return;
      }

      this.socket = new WebSocket(WS_ENDPOINT);

      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        this.emit('connected', { timestamp: new Date().toISOString() });
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.emit(message.type, message.data ?? message);
        } catch {
          return;
        }
      };

      this.socket.onclose = (event) => {
        this.emit('disconnected', { reason: event.reason, timestamp: new Date().toISOString() });
        this.tryReconnect();
      };

      this.socket.onerror = () => {
        this.emit('error', { timestamp: new Date().toISOString() });
      };
    })().finally(() => {
      this.connectPromise = null;
    });

    return this.connectPromise;
  }

  private tryReconnect() {
    if (this.reconnectTimer) {
      return;
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      void this.connect();
    }, this.reconnectDelay);
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.connectPromise = null;
  }

  on(event: string, handler: EventHandler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  off(event: string, handler: EventHandler) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(event);
      }
    }
  }

  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  send(type: string, data?: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, ...data }));
    }
  }

  subscribe(subscriptions: Record<string, boolean>) {
    this.send('subscribe', { subscriptions });
  }

  unsubscribe(messageType: string) {
    this.send('unsubscribe', { message_type: messageType });
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

export const ws = new WebSocketService();
export default ws;
