"""
Market Magic Data Ingestion: Social Media Sentiment Analysis
===========================================================

This module handles the ETL (Extract, Transform, Load) pipeline for social media sentiment data:
1. Extracts social media posts from various platforms (Twitter, Reddit, etc.)
2. Performs sentiment analysis and entity recognition
3. Loads the results into a PostgreSQL database

Author: Tommy Haskell
"""

import pandas as pd
import psycopg2
from psycopg2.extras import Json
import argparse
from datetime import datetime
import requests
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import json
import logging
import os
from dotenv import load_dotenv

from snscrape.modules.reddit import RedditSearchScraper
import regex as re

# Load environment variables
load_dotenv()

###########################################
# Logging Configuration
###########################################
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("social_media_sentiment.log", mode='a')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

###########################################
# Parse Command-Line Arguments
###########################################
parser = argparse.ArgumentParser(description="Market Magic Social Media Sentiment Analysis Script")
parser.add_argument("--twitter_bearer_token", help="Twitter API Bearer Token", required=False)
parser.add_argument("--reddit_client_id", help="Reddit API Client ID", required=False)
parser.add_argument("--reddit_client_secret", help="Reddit API Client Secret", required=False)
parser.add_argument("--reddit_user_agent", help="Reddit API User Agent", required=False)
args = parser.parse_args()

# TODO: Use args or os.getenv for API keys as needed
TWITTER_BEARER_TOKEN = args.twitter_bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
REDDIT_CLIENT_ID = args.reddit_client_id or os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = args.reddit_client_secret or os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = args.reddit_user_agent or os.getenv('REDDIT_USER_AGENT')

logger.info(f"Script started at {datetime.now()}")
logger.info(f"Twitter API Key provided: {'Yes' if TWITTER_BEARER_TOKEN else 'No'}")
logger.info(f"Reddit API Key provided: {'Yes' if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET else 'No'}")

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
    score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
    return score

def extract_entities(text):
    """Extract entities from text (to be implemented with NER model)"""
    # Placeholder for entity recognition
    return {"companies": [], "people": [], "locations": []}

STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BRK.B', 'VZ']
SOCIAL_MEDIA_PLATFORMS = ['Twitter', 'Reddit']

###########################################
# Data Extraction
###########################################
def fetch_twitter_posts(symbol):
    """Fetch recent tweets for a given symbol (placeholder)"""
    logger.info(f"Fetching tweets for {symbol} (placeholder)")
    # TODO: Implement Twitter API integration
    # Return a list of dicts: [{text, datetime, user, platform, url}, ...]
    return []


def fetch_reddit_posts(symbol):
    """Fetch recent Reddit posts for a given symbol (placeholder)"""
    logger.info(f"Fetching Reddit posts for {symbol} (placeholder)")
    # TODO: Implement Reddit API integration
    since = (datetime.now() - datetime.timedelta(hours=24)).strftime('%Y-%m-%d')
    # since (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).strftime('%Y-%m-%d')
    ticker_regex = re.compile(r'\b(' + '|'.join(symbol) + r')\b', re.I)
    
    query = f'subreddit:(stocks OR wallstreetbets) timestamp:{since}..'
    
    scraper = RedditSearchScraper(query)
    def scrape_reddit():
        for item in scraper.get_items():
            if ticker_regex.search(item.content):
                yield {
                    'text': item.content,
                    'datetime': item.date,
                    'user': item.user,
                    'platform': 'Reddit',
                    'url': item.url
                }
    return list(scrape_reddit())



###########################################
# Data Transformation
###########################################
def process_posts(posts):
    """Process social media posts and perform sentiment analysis"""
    logger.info(f"Processing {len(posts)} social media posts")
    processed_data = []
    for post in posts:
        sentiment_score = analyze_sentiment(post['text'])
        keywords = extract_keywords(post['text'])
        entities = extract_entities(post['text'])
        logger.debug(f"Analyzing post: {post['text'][:50]}...")
        logger.debug(f"Sentiment score: {sentiment_score:.3f}, Keywords found: {len(keywords)}")
        processed_data.append({
            'datetime': post['datetime'],
            'platform': post['platform'],
            'user': post.get('user', ''),
            'text': post['text'],
            'url': post.get('url', ''),
            'sentiment_score': sentiment_score,
            'keywords': keywords,
            'entity_recognition': entities
        })
    return processed_data

###########################################
# Database Loading
###########################################
def load_to_database(processed_data):
    """Load processed social media data into PostgreSQL"""
    logger.info("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'asdfghjkl;\''),
        host=os.getenv('POSTGRES_HOST', 'postgres')
    )
    cursor = conn.cursor()
    try:
        # Ensure social media platforms exist in the database
        for platform in set(data['platform'] for data in processed_data):
            cursor.execute("""
                INSERT INTO social_media_platforms (platform_name)
                VALUES (%s)
                ON CONFLICT (platform_name) DO NOTHING
            """, (platform,))
        logger.info("Ensured social media platforms are up to date in the database")
        # Get platform IDs
        cursor.execute("SELECT id, platform_name FROM social_media_platforms")
        platform_ids = {row[1]: row[0] for row in cursor.fetchall()}
        # Insert social media sentiment data
        for data in processed_data: # TODO: Fix solumn names to match schema
            cursor.execute("""
                INSERT INTO social_media_sentiment
                    (datetime, platform_id, user_handle, text, url, sentiment_score, entity_recognition, keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (datetime, text) DO NOTHING
            """, (
                data['datetime'],
                platform_ids[data['platform']],
                data['user'],
                data['text'],
                data['url'],
                data['sentiment_score'],
                json.dumps(data['entity_recognition']),
                Json(data['keywords'])
            ))
            logger.debug(f"Inserted post: {data['text'][:60]}...")
        conn.commit()
        logger.info("Social media sentiment data committed to the database successfully")
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
    logger.info(f"Starting Social Media Sentiment Analysis for {len(STOCK_SYMBOLS)} symbols! Current Time: {datetime.now()}\n")
    all_processed_data = []
    for symbol in STOCK_SYMBOLS:
        logger.info(f"\nProcessing social media for {symbol}...")
        posts = []
        #posts.extend(fetch_twitter_posts(symbol))
        posts.extend(fetch_reddit_posts(symbol))
        if posts:
            processed_data = process_posts(posts)
            all_processed_data.extend(processed_data)
    if all_processed_data:
        logger.info(f"Total processed social media posts: {len(all_processed_data)}")
        load_to_database(all_processed_data)
    else:
        logger.warning("No social media posts were processed. Check data source or connectivity.")

if __name__ == "__main__":
    main()
