# app.py - Partie 1: Configuration et initialisation
from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
from dotenv import load_dotenv
import requests
import json

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)  # Activer CORS pour permettre les requêtes cross-origin

# Configuration de la base de données MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = pymongo.MongoClient(mongo_uri)
db = client["gamma_exposure_db"]
market_data_collection = db["market_data"]
options_data_collection = db["options_data"]
gamma_analysis_collection = db["gamma_analysis"]

# Liste des indices et actions à suivre
INDICES = ["^GSPC", "^NDX", "^DJI"]  # S&P 500, Nasdaq 100, Dow Jones
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
ALL_TICKERS = INDICES + STOCKS

# Constantes pour les calculs de Gamma
DAYS_IN_YEAR = 252
SECONDS_IN_DAY = 86400