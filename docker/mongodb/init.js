-- MongoDB Initialization Script
-- Creates collections and indexes for PipPulse AI

-- Switch to pippulse database
use pippulse;

-- Create raw_news collection
db.createCollection("raw_news");

-- Create indexes for raw_news
db.raw_news.createIndex({ "source": 1 });
db.raw_news.createIndex({ "timestamp": -1 });
db.raw_news.createIndex({ "currency_pairs": 1 });
db.raw_news.createIndex({ "content_hash": 1 }, { unique: true });

-- Create processed_news collection
db.createCollection("processed_news");

-- Create indexes for processed_news
db.processed_news.createIndex({ "timestamp": -1 });
db.processed_news.createIndex({ "currency_pairs": 1 });
db.processed_news.createIndex({ "sentiment.label": 1 });
db.processed_news.createIndex({ "content_hash": 1 }, { unique: true });

-- Create news collection (main collection)
db.createCollection("news");

-- Create indexes for news
db.news.createIndex({ "source": 1 });
db.news.createIndex({ "timestamp": -1 });
db.news.createIndex({ "currency_pairs": 1 });
db.news.createIndex({ "sentiment.label": 1 });
db.news.createIndex({ "content_hash": 1 }, { unique: true });
db.news.createIndex({ "title": "text" });
db.news.createIndex({ "content": "text" });

-- Create signals collection
db.createCollection("signals");

-- Create indexes for signals
db.signals.createIndex({ "currency_pair": 1 });
db.signals.createIndex({ "timestamp": -1 });
db.signals.createIndex({ "direction": 1 });
db.signals.createIndex({ "time_window": 1 });
db.signals.createIndex({ "currency_pair": 1, "time_window": 1, "timestamp": -1 });

-- Create config collection
db.createCollection("config");

-- Create indexes for config
db.config.createIndex({ "type": 1 }, { unique: true });

-- Create backtest_results collection
db.createCollection("backtest_results");

-- Create indexes for backtest_results
db.backtest_results.createIndex({ "currency_pair": 1 });
db.backtest_results.createIndex({ "start_date": -1 });
db.backtest_results.createIndex({ "end_date": -1 });

-- Insert default configuration
db.config.insertOne({
    type: "thresholds",
    thresholds: {
        "EUR/USD": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        },
        "GBP/USD": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        },
        "USD/JPY": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        },
        "USD/CHF": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        },
        "AUD/USD": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        },
        "USD/CAD": {
            buy_threshold: 0.3,
            sell_threshold: -0.3,
            confidence_threshold: 0.6,
            time_decay_lambda: 0.1
        }
    },
    created_at: new Date(),
    updated_at: new Date()
});

db.config.insertOne({
    type: "source_weights",
    weights: {
        "newsapi": 0.9,
        "twitter": 0.7,
        "reddit": 0.6,
        "telegram": 0.5
    },
    created_at: new Date(),
    updated_at: new Date()
});

db.config.insertOne({
    type: "time_windows",
    windows: {
        "15min": 15,
        "1hour": 60,
        "4hour": 240
    },
    created_at: new Date(),
    updated_at: new Date()
});

print("MongoDB initialization completed successfully!");
