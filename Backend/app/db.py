import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable or default to local MongoDB
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# Get database name from environment variable or default
MONGO_DB = os.getenv("MONGODB_DB", "video_retrieval")

# Create MongoDB client
client = MongoClient(MONGO_URI)

# Access the database
db = client[MONGO_DB]

# Define collections used in the project
chunks_collection = db["chunks"]