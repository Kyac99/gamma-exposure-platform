# app.py
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

def calculate_gamma(options_chain, spot_price, risk_free_rate=0.05):
    """
    Calcule le Gamma Exposure pour une chaîne d'options
    """
    calls = options_chain['calls']
    puts = options_chain['puts']
    
    # Traitement des calls
    calls_df = pd.DataFrame(calls)
    if not calls_df.empty:
        # Calculer le gamma pour les calls
        calls_df['gamma'] = calls_df.apply(lambda row: 
            calculate_option_gamma(
                S=spot_price,
                K=row['strike'],
                T=(datetime.strptime(row['expiration'], '%Y-%m-%d') - datetime.now()).days / DAYS_IN_YEAR,
                r=risk_free_rate,
                sigma=row['impliedVolatility'],
                option_type='call'
            ), axis=1)
        calls_df['gammaExposure'] = calls_df['gamma'] * calls_df['openInterest'] * spot_price * spot_price * 0.01
    else:
        calls_df = pd.DataFrame(columns=['gammaExposure'])
        
    # Traitement des puts
    puts_df = pd.DataFrame(puts)
    if not puts_df.empty:
        # Calculer le gamma pour les puts
        puts_df['gamma'] = puts_df.apply(lambda row: 
            calculate_option_gamma(
                S=spot_price,
                K=row['strike'],
                T=(datetime.strptime(row['expiration'], '%Y-%m-%d') - datetime.now()).days / DAYS_IN_YEAR,
                r=risk_free_rate,
                sigma=row['impliedVolatility'],
                option_type='put'
            ), axis=1)
        puts_df['gammaExposure'] = puts_df['gamma'] * puts_df['openInterest'] * spot_price * spot_price * 0.01 * -1  # Négatif pour les puts
    else:
        puts_df = pd.DataFrame(columns=['gammaExposure'])
    
    # Agrégation par strike
    all_options = pd.concat([calls_df, puts_df])
    gamma_by_strike = all_options.groupby('strike')['gammaExposure'].sum().reset_index()
    
    # Calcul du gamma net total
    net_gamma = all_options['gammaExposure'].sum()
    
    # Trouver les niveaux de gamma significatifs
    gamma_levels = identify_gamma_levels(gamma_by_strike)
    
    return {
        'netGamma': float(net_gamma),
        'gammaByStrike': gamma_by_strike.to_dict('records'),
        'gammaLevels': gamma_levels
    }

def calculate_option_gamma(S, K, T, r, sigma, option_type):
    """
    Calculer le gamma d'une option en utilisant le modèle Black-Scholes
    
    S: prix du sous-jacent
    K: prix d'exercice
    T: temps jusqu'à l'expiration (en années)
    r: taux sans risque
    sigma: volatilité implicite
    option_type: 'call' ou 'put'
    """
    from scipy.stats import norm
    
    if T <= 0 or sigma <= 0:
        return 0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    return float(gamma)

def identify_gamma_levels(gamma_by_strike):
    """
    Identifie les niveaux de gamma significatifs
    """
    if gamma_by_strike.empty:
        return []
    
    # Tri par valeur absolue de gamma exposure
    sorted_gamma = gamma_by_strike.sort_values(by='gammaExposure', key=abs, ascending=False)
    
    # Prendre les 5 niveaux de gamma les plus significatifs
    top_levels = sorted_gamma.head(5).to_dict('records')
    
    return top_levels