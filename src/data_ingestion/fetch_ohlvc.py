"""
Market Magic Data Ingestion: Fetch Data
=====================================

This module handles the ETL (Extract, Transform, Load) pipeline for market data:
1. Extracts data from Google Sheets
2. Transforms it into properly formatted dataframes
3. Loads it into a PostgreSQL database

Author: Tommy Haskell
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
import psycopg2
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

###########################################
# Parse Command-Line Arguments
###########################################
parser = argparse.ArgumentParser(description="Market Magic Data Ingestion Script")
parser.add_argument("--creds", help="Path to the Google API credentials JSON file", default="credentials.json")
args = parser.parse_args()

###########################################
# Google Sheets Authentication & Setup
###########################################

# Define the scope for Google Sheets API access
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Get credentials
creds = ServiceAccountCredentials.from_json_keyfile_name(args.creds, scope)
client = gspread.authorize(creds)

###########################################
# Data Extraction
###########################################

try:
    ohlvc_sheet = client.open("Market Magic Data Source").worksheet("OHLVC")
    import datetime
    print(f"\n**\nData Fetched Successfully! Current Time: {datetime.datetime.now()}\n")
    
    # Convert sheet data to pandas DataFrame
    ohlvc_data = pd.DataFrame(ohlvc_sheet.get_all_values())
    # Set proper column headers from row 3
    ohlvc_data.columns = ohlvc_data.iloc[2]
    # Remove the first 3 rows (including the header row we just used)
    ohlvc_data = ohlvc_data.iloc[3:].reset_index(drop=True)

except gspread.exceptions.SpreadsheetNotFound:
    print("Error: Spreadsheet not found. Please ensure:")
    print("1. The spreadsheet 'Market Magic Data Source' exists")
    print("2. It's shared with the service account email in credentials.json")
    print("3. The credentials.json file is valid and has correct permissions")

###########################################
# Data Transformation
###########################################

# Split main dataframe into individual company dataframes
# Each company has 7 columns: Symbol, Date, Open, High, Low, Close, Volume
company_dataframes = [
    ohlvc_data.iloc[:, :7].copy(),      # Apple
    ohlvc_data.iloc[:, 7:14].copy(),    # Microsoft
    ohlvc_data.iloc[:, 14:21].copy(),   # Google
    ohlvc_data.iloc[:, 21:28].copy(),   # Amazon
    ohlvc_data.iloc[:, 28:35].copy(),   # Meta
    ohlvc_data.iloc[:, 35:42].copy(),   # Tesla
    ohlvc_data.iloc[:, 42:49].copy(),   # NVIDIA
    ohlvc_data.iloc[:, 49:56].copy(),   # JPMorgan
    ohlvc_data.iloc[:, 56:63].copy(),   # Berkshire
    ohlvc_data.iloc[:, 63:70].copy()    # Verizon
]

# Clean data: Remove rows with invalid or empty values
for company in company_dataframes:
    # Convert Open column to numeric for filtering
    company['Open'] = company['Open'].replace('', '0')
    company['Open'] = pd.to_numeric(company['Open'], errors='coerce')
    
    # Remove rows where Open is NaN or 0
    company.drop(company[company['Open'].isna() | (company['Open'] == 0)].index, inplace=True)
    company.reset_index(drop=True, inplace=True)

print("\nRows after filtering:")
for company in company_dataframes:
    print(f"{company['Symbol'].iloc[0]}: {len(company)} rows")

# Convert data types for each company dataframe
for company in company_dataframes:
    try:
        # Clean and standardize numeric columns
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            company[col] = company[col].replace(['', '-'], '0')
            
        # Convert columns to appropriate data types
        company['Date'] = pd.to_datetime(company['Date'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        company['Volume'] = pd.to_numeric(company['Volume'], errors='coerce').fillna(0).astype(int)
        
        # Convert price columns to float
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            company[col] = pd.to_numeric(company[col], errors='coerce').fillna(0).astype(float)
            
    except Exception as e:
        print(f"Error processing data: {e}")
        print(f"Problematic columns:\n{company.dtypes}")
        continue

print("\nDATA TYPE CONVERSION DONE!\n")

# Verify the conversions
for company in company_dataframes:
    print(f"\nDataframe info for {company['Symbol'].iloc[0]}:")
    print(company.dtypes)

###########################################
# Database Loading
###########################################

# Connect to PostgreSQL using environment variables
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB', 'postgres'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'asdfghjkl;\''),
    host=os.getenv('POSTGRES_HOST', 'postgres')  # Uses service name from docker-compose file
)
cursor = conn.cursor()
print(f"\n**\nDatabase connection successful!\n**\n")

# Insert or update data for each company
for company in company_dataframes:
    for index, row in company.iterrows():
        cursor.execute("""
            INSERT INTO market_data_partitioned 
                (symbol, datetime, open_price, high_price, low_price, close_price, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, datetime) DO UPDATE 
            SET close_price = EXCLUDED.close_price, 
                volume = EXCLUDED.volume;
        """, (
            row['Symbol'],
            row['Date'],
            row['Open'],
            row['High'],
            row['Low'],
            row['Close'],
            row['Volume']
        ))

conn.commit()
cursor.close()
conn.close()