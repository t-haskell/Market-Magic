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
        # This is a placeholder - you'll need to implement actual API calls
        # based on the news source's API
        response = requests.get(f"{NEWS_SOURCES[source]}{symbol}")
        if response.status_code == 200:
            # Parse articles using newspaper3k
            # This is a simplified example
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
    except Exception as e:
        print(f"Error fetching news for {symbol} from {source}: {e}")
    return articles

###########################################
# Data Transformation
###########################################
def process_articles(articles):
    """Process articles and perform sentiment analysis"""
    processed_data = []
    for article in articles:
        sentiment_score = analyze_sentiment(article['text'])
        keywords = extract_keywords(article['text'])
        entities = extract_entities(article['text'])
        
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
    conn = psycopg2.connect(
        dbname="postgres",
        # dbname="postgres",
        user="postgres",
        password="asdfghjkl;'",
        # host="postgres"
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
        
        conn.commit()
        print("News sentiment data loaded successfully!")
    except Exception as e:
        print(f"Error loading data to database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

###########################################
# Main Execution
###########################################
def main():
    print(f"\n**\nStarting News Sentiment Analysis! Current Time: {datetime.now()}\n")
    
    all_processed_data = []
    for symbol in STOCK_SYMBOLS:
        print(f"\nProcessing news for {symbol}...")
        for source in NEWS_SOURCES:
            articles = fetch_news_articles(symbol, source)
            if articles:
                processed_data = process_articles(articles)
                all_processed_data.extend(processed_data)
    
    if all_processed_data:
        load_to_database(all_processed_data)
    else:
        print("No news articles were processed.")

if __name__ == "__main__":
    main() 