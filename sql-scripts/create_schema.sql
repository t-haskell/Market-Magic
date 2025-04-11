-- MARKET DATA
CREATE TABLE market_data_partitioned (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume BIGINT,
    sma_50 NUMERIC,  
    sma_200 NUMERIC, 
    rsi NUMERIC,
    macd NUMERIC,
    UNIQUE(symbol)
) PARTITION BY LIST (symbol);

-- NEWS SENTIMENT
CREATE TABLE news_sources (
    id SERIAL PRIMARY KEY,
    source_name TEXT UNIQUE
);

CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    source_id INT,
    title TEXT,
    sentiment_score NUMERIC,
    entity_recognition JSONB,
    keywords TEXT[],
    UNIQUE(datetime, title),
    FOREIGN KEY (source_id) REFERENCES news_sources(id)
);

-- SOCIAL MEDIA SENTIMENT
CREATE TABLE social_media_platforms (
    id SERIAL PRIMARY KEY,
    platform_name TEXT UNIQUE CHECK (platform_name IN ('twitter', 'reddit'))
);

CREATE TABLE social_media_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    platform_id INT,
    post_text TEXT,
    sentiment_score NUMERIC,
    engagement INT,
    author TEXT,
    UNIQUE(datetime, post_text),
    FOREIGN KEY (platform_id) REFERENCES social_media_platforms(id)
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
    FOREIGN KEY (symbol) REFERENCES market_data_partitioned(symbol),
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id)
);

-- INDEXES
CREATE INDEX idx_market_data_datetime ON market_data_partitioned(datetime);
CREATE INDEX idx_news_keywords ON news_sentiment USING GIN (keywords);
CREATE INDEX idx_social_post_text ON social_media_sentiment USING GIN (to_tsvector('english', post_text));
CREATE INDEX idx_satellite_features ON satellite_data USING GIN (extracted_features);
CREATE INDEX idx_predictions_symbol_datetime ON model_predictions(symbol, datetime);