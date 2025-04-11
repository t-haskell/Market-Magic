-- TABLE CREATION

CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume BIGINT,
    sma_50 NUMERIC,  -- Example: Simple Moving Average
    sma_200 NUMERIC, 
    rsi NUMERIC,  -- Relative Strength Index
    macd NUMERIC,  -- MACD indicator
    UNIQUE(symbol, datetime)
);

CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    source TEXT,
    title TEXT,
    sentiment_score NUMERIC,  -- [-1 to 1] sentiment polarity
    entity_recognition JSONB,  -- Named entities detected (JSON format)
    keywords TEXT[],
    UNIQUE(datetime, title)
);

CREATE TABLE social_media_sentiment (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    platform TEXT CHECK (platform IN ('twitter', 'reddit')),
    post_text TEXT,
    sentiment_score NUMERIC,  -- [-1 to 1]
    engagement INT,  -- Likes/retweets/upvotes
    author TEXT,
    UNIQUE(datetime, post_text)
);

CREATE TABLE satellite_data (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    location TEXT,
    image_url TEXT,  -- Link to stored image (Cloud Storage / S3)
    extracted_features JSONB,  -- Example: Traffic density, farmland changes
    UNIQUE(datetime, location)
);

CREATE TABLE model_predictions (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    predicted_price NUMERIC NOT NULL,
    confidence_score NUMERIC CHECK (confidence_score BETWEEN 0 AND 1),
    model_version TEXT,
    UNIQUE(symbol, datetime, model_version)
);




-- INDEXING THE TIME-SERIES DATA
CREATE INDEX idx_market_data_datetime ON market_data(datetime);
CREATE INDEX idx_news_sentiment_datetime ON news_sentiment(datetime);
CREATE INDEX idx_social_sentiment_datetime ON social_media_sentiment(datetime);
CREATE INDEX idx_predictions_symbol_datetime ON model_predictions(symbol, datetime);




-- FK
ALTER TABLE model_predictions 
ADD CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
REFERENCES market_data(symbol);
