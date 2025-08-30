import os
import sys
import traceback
import pandas as pd
from pymongo import MongoClient

def init_mongodb():
    """Initialize MongoDB connection"""
    try:
        print("Attempting to connect to MongoDB...")
        client = MongoClient("mongodb://localhost:27017")
        db = client["afrahkoum"]
        print("MongoDB connection established successfully")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)

def upload_csv_to_mongodb(csv_path, collection_name='ict_inventory'):
    """Upload CSV data to MongoDB"""
    try:
        # Read CSV file
        print(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"Found {len(df)} rows in CSV")
        print("Initializing MongoDB connection...")

        # Initialize MongoDB
        db = init_mongodb()
        collection = db[collection_name]

        print("Converting data to MongoDB format...")
        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient='records')

        # Insert records into MongoDB
        print(f"Inserting {len(records)} records into MongoDB collection '{collection_name}'...")
        result = collection.insert_many(records)
        print(f"Successfully inserted {len(result.inserted_ids)} records into MongoDB")

        return True
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_path}' not found!")
        return False
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    CSV_FILE = "ICT Inventory.csv"

    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found in the current directory!")
        print("Make sure the CSV file is in the same directory as this script.")
        print("Current directory:", os.getcwd())
        sys.exit(1)

    success = upload_csv_to_mongodb(CSV_FILE)
    if not success:
        print("Upload failed!")
        sys.exit(1)
    else:
        print("✅ Upload completed successfully!")