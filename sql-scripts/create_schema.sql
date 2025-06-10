-- MARKET DATA
CREATE TABLE market_data_partitioned (
    id SERIAL,
    symbol TEXT NOT NULL,
    datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    open_price NUMERIC(19,4),
    high_price NUMERIC(19,4),
    low_price NUMERIC(19,4),
    close_price NUMERIC(19,4),
    volume BIGINT,
    sma_50 NUMERIC(19,4),
    sma_200 NUMERIC(19,4),
    rsi NUMERIC(5,2),
    macd NUMERIC(19,4),
    CONSTRAINT market_data_symbol_datetime_key UNIQUE(symbol, datetime),
    PRIMARY KEY (symbol, id)
) PARTITION BY LIST (symbol);

-- Explicit partitions for specific stock tickers
CREATE TABLE market_data_aapl PARTITION OF market_data_partitioned
    FOR VALUES IN ('AAPL');

CREATE TABLE market_data_msft PARTITION OF market_data_partitioned
    FOR VALUES IN ('MSFT');

CREATE TABLE market_data_googl PARTITION OF market_data_partitioned
    FOR VALUES IN ('GOOGL');

CREATE TABLE market_data_amzn PARTITION OF market_data_partitioned
    FOR VALUES IN ('AMZN');

CREATE TABLE market_data_meta PARTITION OF market_data_partitioned
    FOR VALUES IN ('META');

CREATE TABLE market_data_tsla PARTITION OF market_data_partitioned
    FOR VALUES IN ('TSLA');

CREATE TABLE market_data_nvda PARTITION OF market_data_partitioned
    FOR VALUES IN ('NVDA');

CREATE TABLE market_data_jpm PARTITION OF market_data_partitioned
    FOR VALUES IN ('JPM');

CREATE TABLE market_data_brkb PARTITION OF market_data_partitioned
    FOR VALUES IN ('BRK.B');

CREATE TABLE market_data_vz PARTITION OF market_data_partitioned
    FOR VALUES IN ('VZ');

-- Default partition: catches any rows with a ticker not explicitly defined above
CREATE TABLE market_data_default PARTITION OF market_data_partitioned DEFAULT;

-- NEWS SENTIMENT
CREATE TABLE news_sources (
    id SERIAL PRIMARY KEY,
    source_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    source_id INT NOT NULL,
    title TEXT NOT NULL,
    sentiment_score NUMERIC(4,3) CHECK (sentiment_score BETWEEN -1 AND 1),
    entity_recognition JSONB,
    keywords JSONB,
    CONSTRAINT news_datetime_title_key UNIQUE(datetime, title),
    CONSTRAINT fk_news_source FOREIGN KEY (source_id) REFERENCES news_sources(id)
);

-- SOCIAL MEDIA SENTIMENT
CREATE TABLE social_media_platforms (
    id SERIAL PRIMARY KEY,
    platform_name TEXT NOT NULL UNIQUE,
    CONSTRAINT valid_platform CHECK (platform_name IN ('twitter', 'reddit'))
);

CREATE TABLE social_media_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    platform_id INT NOT NULL,
    post_text TEXT NOT NULL,
    sentiment_score NUMERIC(4,3) CHECK (sentiment_score BETWEEN -1 AND 1),
    engagement INT NOT NULL DEFAULT 0,
    author TEXT NOT NULL,
    CONSTRAINT social_datetime_post_key UNIQUE(datetime, post_text),
    CONSTRAINT fk_platform FOREIGN KEY (platform_id) REFERENCES social_media_platforms(id)
);

-- SATELLITE DATA
CREATE TABLE satellite_data (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    location TEXT,
    image_url TEXT,
    image_hash TEXT UNIQUE,
    extracted_features JSONB,
    UNIQUE(datetime, location)
);

-- MODEL PREDICTIONS
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    version TEXT UNIQUE
);

CREATE TABLE model_predictions (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    predicted_price NUMERIC NOT NULL,
    confidence_score NUMERIC CHECK (confidence_score BETWEEN 0 AND 1),
    model_version_id INT,
    UNIQUE(symbol, datetime, model_version_id),
    -- FOREIGN KEY (symbol) REFERENCES market_data_partitioned(symbol),
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id)
);

-- INDEXES
CREATE INDEX idx_market_data_datetime ON market_data_partitioned(datetime DESC);
CREATE INDEX idx_news_datetime ON news_sentiment(datetime DESC);
CREATE INDEX idx_news_keywords ON news_sentiment USING GIN (keywords);
CREATE INDEX idx_social_sentiment ON social_media_sentiment(sentiment_score);
CREATE INDEX idx_social_post_text ON social_media_sentiment USING GIN (to_tsvector('english', post_text));
CREATE INDEX idx_satellite_features ON satellite_data USING GIN (extracted_features);
CREATE INDEX idx_predictions_symbol_datetime ON model_predictions(symbol, datetime DESC);