-- PostgreSQL Initialization Script
-- Creates tables and indexes for PipPulse AI

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table (for future authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create backtest_runs table
CREATE TABLE IF NOT EXISTS backtest_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency_pair VARCHAR(20) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    initial_capital DECIMAL(15, 2) NOT NULL,
    final_capital DECIMAL(15, 2) NOT NULL,
    total_return DECIMAL(10, 4) NOT NULL,
    win_rate DECIMAL(5, 2) NOT NULL,
    average_risk_reward DECIMAL(10, 4) NOT NULL,
    sharpe_ratio DECIMAL(10, 4) NOT NULL,
    max_drawdown DECIMAL(10, 4) NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    confidence_calibration JSONB,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes on backtest_runs
CREATE INDEX IF NOT EXISTS idx_backtest_runs_currency_pair ON backtest_runs(currency_pair);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_dates ON backtest_runs(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_created_at ON backtest_runs(created_at DESC);

-- Create system_config table
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on system_config
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- Insert default system configurations
INSERT INTO system_config (config_key, config_value, description) VALUES
('signal_thresholds', '{
    "EUR/USD": {"buy_threshold": 0.3, "sell_threshold": -0.3, "confidence_threshold": 0.6},
    "GBP/USD": {"buy_threshold": 0.3, "sell_threshold": -0.3, "confidence_threshold": 0.6},
    "USD/JPY": {"buy_threshold": 0.3, "sell_threshold": -0.3, "confidence_threshold": 0.6}
}', 'Signal generation thresholds per currency pair'),
('source_weights', '{
    "newsapi": 0.9,
    "twitter": 0.7,
    "reddit": 0.6,
    "telegram": 0.5
}', 'Source credibility weights'),
('time_windows', '{
    "15min": 15,
    "1hour": 60,
    "4hour": 240
}', 'Time window configurations in minutes')
ON CONFLICT (config_key) DO NOTHING;

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for backtest summary
CREATE OR REPLACE VIEW backtest_summary AS
SELECT
    currency_pair,
    COUNT(*) as total_runs,
    AVG(total_return) as avg_return,
    AVG(win_rate) as avg_win_rate,
    AVG(sharpe_ratio) as avg_sharpe_ratio,
    MAX(max_drawdown) as worst_drawdown,
    MAX(created_at) as last_run
FROM backtest_runs
GROUP BY currency_pair;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pippulse;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pippulse;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO pippulse;

COMMIT;
