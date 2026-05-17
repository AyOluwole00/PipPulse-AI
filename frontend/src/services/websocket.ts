import type { WebSocketMessage } from '@/types';

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

  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
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
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    this.socket.onclose = (event) => {
      this.emit('disconnected', { reason: event.reason, timestamp: new Date().toISOString() });
      this.tryReconnect();
    };

    this.socket.onerror = () => {
      this.emit('error', { timestamp: new Date().toISOString() });
    };
  }

  private tryReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    this.reconnectAttempts += 1;
    setTimeout(() => this.connect(), this.reconnectDelay);
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
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
