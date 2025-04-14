"""
Market Magic Data Ingestion: News Sentiment Analysis
=================================================

This module handles the ETL (Extract, Transform, Load) pipeline for news sentiment data:
1. Extracts news articles from various sources
2. Performs sentiment analysis and entity recognition
3. Loads the results into a PostgreSQL database

Author: Tommy Haskell
"""

import pandas as pd
import psycopg2
import argparse
from datetime import datetime
import requests
from newspaper import Article
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import json
import logging

###########################################
# Logging Configuration
###########################################
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("news_sentiment.log", mode='a')  # File logging
    ]
)

logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

###########################################
# Parse Command-Line Arguments
###########################################
parser = argparse.ArgumentParser(description="Market Magic News Sentiment Analysis Script")
parser.add_argument("--api_key", help="API key for news sources", required=False)
args = parser.parse_args()

logger.info(f"Script started at {datetime.now()}")
logger.info(f"API Key provided: {'Yes' if args.api_key else 'No'}")

###########################################
# News Sources Configuration
###########################################
NEWS_SOURCES = {
    'Reuters': 'https://www.reuters.com/markets/companies/',
    'Bloomberg': 'https://www.bloomberg.com/markets/stocks',
    'CNBC': 'https://www.cnbc.com/markets/'
}

STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BRK.B', 'VZ']

###########################################
# Sentiment Analysis Setup
###########################################
sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
stop_words = set(stopwords.words('english'))

def extract_keywords(text):
    """Extract keywords from text using NLTK"""
    words = word_tokenize(text.lower())
    return [word for word in words if word.isalpha() and word not in stop_words]

def analyze_sentiment(text):
    """Analyze sentiment of text using transformers"""
    result = sentiment_analyzer(text)[0]
    # Convert sentiment score to -1 to 1 range
    score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
    return score

def extract_entities(text):
    """Extract entities from text (to be implemented with NER model)"""
    # Placeholder for entity recognition
    return {"companies": [], "people": [], "locations": []}

###########################################
# Data Extraction
###########################################
def fetch_news_articles(symbol, source):
    """Fetch news articles for a given symbol from a source"""
    articles = []
    try:
        logger.info(f"Fetching articles for {symbol} from {source}")
        logger.debug(f"Requesting URL: {NEWS_SOURCES[source]}{symbol}")
        
        # This is a placeholder to implement actual news source API's TODO
        response = requests.get(f"{NEWS_SOURCES[source]}{symbol}")
        if response.status_code == 200:
            # Simplified parsing of articles, could be refined TODO
            article = Article(response.url)
            article.download()
            article.parse()
            
            articles.append({
                'title': article.title,
                'text': article.text,
                'url': article.url,
                'datetime': article.publish_date or datetime.now(),
                'source': source
            })
            logger.info(f"Article fetched: {article.title[:60]}... from {source}")
    except Exception as e:
        logger.error(f"Failed to fetch or parse article for {symbol} from {source}: {e}")
    return articles

###########################################
# Data Transformation
###########################################
def process_articles(articles):
    """Process articles and perform sentiment analysis"""

    logger.info(f"Processing {len(articles)} articles")

    processed_data = []
    for article in articles:
        sentiment_score = analyze_sentiment(article['text'])
        keywords = extract_keywords(article['text'])
        entities = extract_entities(article['text'])
        
        logger.debug(f"Analyzing article: {article['title'][:50]}...")
        logger.debug(f"Sentiment score: {sentiment_score:.3f}, Keywords found: {len(keywords)}")

        processed_data.append({
            'datetime': article['datetime'],
            'source': article['source'],
            'title': article['title'],
            'sentiment_score': sentiment_score,
            'keywords': json.dumps(keywords),
            'entity_recognition': entities
        })
    return processed_data

###########################################
# Database Loading
###########################################
def load_to_database(processed_data):
    """Load processed news data into PostgreSQL"""

    logger.info("Connecting to PostgreSQL database...")

    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="asdfghjkl;'",
        # host="postgres"   # TODO For Jenkins pipeline with Postgres instance in Docker container
        host="localhost"
    )
    cursor = conn.cursor()
    
    try:
        # First, ensure news sources exist in the database
        for source in NEWS_SOURCES.keys():
            cursor.execute("""
                INSERT INTO news_sources (source_name)
                VALUES (%s)
                ON CONFLICT (source_name) DO NOTHING
            """, (source,))
        
        logger.info("Ensured news sources are up to date in the database")
        
        # Get source IDs
        cursor.execute("SELECT id, source_name FROM news_sources")
        source_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Insert news sentiment data
        for data in processed_data:
            cursor.execute("""
                INSERT INTO news_sentiment 
                    (datetime, source_id, title, sentiment_score, entity_recognition, keywords)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (datetime, title) DO NOTHING
            """, (
                data['datetime'],
                source_ids[data['source']],
                data['title'],
                data['sentiment_score'],
                json.dumps(data['entity_recognition']),
                data['keywords']
            ))
        
            logger.debug(f"Inserted article: {data['title'][:60]}...")
        
        conn.commit()
        
        logger.info("News sentiment data committed to the database successfully")
    
    except Exception as e:
        logger.error(f"Database insertion failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

###########################################
# Main Execution
###########################################
def main():
    logger.info(f"Starting News Sentiment Analysis for {len(STOCK_SYMBOLS)} symbols! Current Time: {datetime.now()}\n")
    
    all_processed_data = []
    for symbol in STOCK_SYMBOLS:
        logger.info(f"\nProcessing news for {symbol}...")
        for source in NEWS_SOURCES:
            articles = fetch_news_articles(symbol, source)
            if articles:
                processed_data = process_articles(articles)
                all_processed_data.extend(processed_data)
    
    if all_processed_data:
        logger.info(f"Total processed articles: {len(all_processed_data)}")
        load_to_database(all_processed_data)
    else:
        logger.warning("No articles were processed. Check data source or connectivity.")

if __name__ == "__main__":
    main()