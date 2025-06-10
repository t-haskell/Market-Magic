# Market Magic ML

An advanced financial market prediction system that combines traditional market data with alternative data sources to provide comprehensive market insights and predictions.

## 🎯 Project Overview

Market Magic ML is a sophisticated financial analysis platform that integrates multiple data sources to provide a holistic view of market movements. The system combines traditional market data (OHLVC) with alternative data sources like news sentiment analysis to generate more accurate market predictions.

### Key Features

- **Multi-Source Data Integration**
  - Traditional market data (OHLVC) from Google Sheets
  - News sentiment analysis from multiple sources via NewsAPI
  - Social media sentiment analysis (schema prepared)
  - Satellite data analysis (schema prepared)

- **Advanced Analytics**
  - Sentiment analysis using DistilBERT transformer model
  - Technical indicators (SMA, RSI, MACD) - schema prepared
  - Entity recognition and keyword extraction using NLTK
  - Machine learning-based price predictions (schema prepared)

- **Scalable Architecture**
  - Containerized deployment with Docker
  - CI/CD pipeline with Jenkins
  - PostgreSQL database with partitioned tables
  - Poetry for dependency management

## 🛠️ Technology Stack

### Backend
- **Python 3.10+**
  - pandas: Data manipulation and analysis
  - transformers: NLP and sentiment analysis (DistilBERT)
  - nltk: Natural language processing
  - newspaper3k: Article parsing
  - psycopg2: PostgreSQL database interface
  - gspread: Google Sheets API integration
  - newsapi-python: News API integration

### Database
- **PostgreSQL 14**
  - Partitioned tables for efficient data storage
  - JSONB support for flexible data structures
  - GIN indexes for full-text search
  - Foreign key constraints for data integrity

### Infrastructure
- **Docker & Docker Compose**
  - Jenkins container for CI/CD
  - PostgreSQL container
  - Volume management for data persistence

### Development Tools
- **Poetry**
  - Dependency management
  - Virtual environment handling
  - Build system

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Docker and Docker Compose
- Poetry
- Google Sheets API credentials
- NewsAPI.org API key

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/thask/MarketMagicML.git
   cd MarketMagicML
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   GOOGLE_CREDS_JSON=path_to_credentials.json
   NEWS_API_KEY=your_news_api_key
   ```

4. **Set up Google Sheets credentials**
   - Place your `credentials.json` file in the root directory
   - Ensure the Google Sheets document "Market Magic Data Source" is shared with the service account

5. **Start the Docker containers**
   ```bash
   docker-compose up -d
   ```

6. **Initialize the database**
   ```bash
   docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/create_schema.sql
   ```

## 🚀 Usage

### Data Ingestion

The system includes two main data ingestion scripts:

1. **Market Data Collection**
   ```bash
   poetry run python src/data_ingestion/fetch_ohlvc.py --creds path_to_credentials.json
   ```

2. **News Sentiment Analysis**
   ```bash
   poetry run python src/data_ingestion/fetch_news_sentiment.py --api_key your_news_api_key
   ```

### Automated Pipeline

The Jenkins pipeline automatically runs these scripts daily at 9 AM UTC. The pipeline:
1. Sets up the Python environment
2. Runs market data collection from Google Sheets
3. Performs news sentiment analysis using NewsAPI
4. Loads data into the PostgreSQL database

### Supported Stocks

The system currently tracks the following stocks:
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- META (Meta)
- TSLA (Tesla)
- NVDA (NVIDIA)
- JPM (JPMorgan)
- BRK.B (Berkshire Hathaway)
- VZ (Verizon)

## 📊 Database Schema

The database is designed with several key tables:

- `market_data_partitioned`: Partitioned table for OHLVC data with technical indicators
- `news_sources`: Reference table for news sources
- `news_sentiment`: News articles with sentiment scores and keyword extraction
- `social_media_platforms`: Reference table for social media platforms
- `social_media_sentiment`: Social media posts and sentiment (schema ready)
- `satellite_data`: Satellite imagery and extracted features (schema ready)
- `model_versions`: Reference table for ML model versions
- `model_predictions`: ML model predictions and confidence scores (schema ready)

## 🔧 Configuration

### Jenkins Setup
- Jenkins runs on port 8080
- PostgreSQL runs on port 5433
- Credentials are managed through Jenkins secrets:
  - `GOOGLE_CREDS_JSON`: Google Sheets API credentials
  - `NEWS_API_KEY`: NewsAPI.org API key

### Data Sources
- **Google Sheets**: Contains OHLVC data for 10 major stocks
- **NewsAPI.org**: Provides news articles for sentiment analysis
- **PostgreSQL**: Stores all processed data with proper indexing

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Tommy Haskell** - *Initial work* - [thask](https://github.com/thask)

## 🙏 Acknowledgments

- Thanks to all contributors and supporters of the project
- Special thanks to the open-source community for the amazing tools and libraries

## 📞 Contact

For questions or support, please contact:
- Email: tommyhaskell3@gmail.com
- GitHub: [thask](https://github.com/thask)