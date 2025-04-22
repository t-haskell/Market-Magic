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
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

###########################################
# Logging Configuration
###########################################
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Standard out displays only INFO-level log messages
file_handler = logging.FileHandler("news_sentiment.log", mode='a')
file_handler.setLevel(logging.DEBUG)    # Log file will have all log messages including DEBUG

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

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

# Initialize NewsAPI client (requires --api_key)
if not args.api_key:
    logger.error("NewsAPI.org API key is required for article fetching")
    exit(1)
newsapi = NewsApiClient(api_key=args.api_key)

logger.info(f"Script started at {datetime.now()}")
logger.info(f"API Key provided: {'Yes' if args.api_key else 'No'}")

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
def fetch_news_articles(symbol):
    """Fetch news articles for a given symbol using NewsAPI.org"""
    articles = []
    logger.info(f"Fetching articles for {symbol} via NewsAPI")
    try:
        response = newsapi.get_everything(
            q=symbol,
            language='en',
            sort_by='publishedAt',
            page_size=100
        )
        for item in response.get('articles', []):
            articles.append({
                'title': item['title'],
                'text': item.get('description') or '',
                'url': item['url'],
                'datetime': datetime.fromisoformat(item['publishedAt'].rstrip('Z')),
                'source': item['source']['name']
            })
        if not articles:
            logger.info(f"No articles returned for {symbol}")
    except Exception as e:
        logger.error(f"Failed to fetch articles for {symbol}: {e}")
    return articles

STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BRK.B', 'VZ']

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
        dbname=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'asdfghjkl;\''),
        host=os.getenv('POSTGRES_HOST', 'postgres')  # Uses service name from docker-compose file
    )
    cursor = conn.cursor()
    
    try:
        # First, ensure news sources exist in the database
        for source in set(data['source'] for data in processed_data):
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
        articles = fetch_news_articles(symbol)
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
