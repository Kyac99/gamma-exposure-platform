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

def fetch_market_data():
    """
    Récupère les données de marché pour tous les tickers
    """
    try:
        logger.info("Fetching market data...")
        all_data = {}
        
        # Utiliser yfinance pour récupérer les données de marché
        data = yf.download(ALL_TICKERS, period="1d")
        
        # Traiter les données pour chaque ticker
        for ticker in ALL_TICKERS:
            try:
                # Récupérer la dernière barre
                last_bar = {
                    'ticker': ticker,
                    'timestamp': datetime.now(),
                    'open': float(data['Open'][ticker].iloc[-1]),
                    'high': float(data['High'][ticker].iloc[-1]),
                    'low': float(data['Low'][ticker].iloc[-1]),
                    'close': float(data['Close'][ticker].iloc[-1]),
                    'volume': float(data['Volume'][ticker].iloc[-1]),
                    'change': float((data['Close'][ticker].iloc[-1] / data['Open'][ticker].iloc[-1] - 1) * 100)
                }
                
                # Stockage dans MongoDB
                market_data_collection.update_one(
                    {'ticker': ticker},
                    {'$set': last_bar},
                    upsert=True
                )
                
                all_data[ticker] = last_bar
                logger.info(f"Updated market data for {ticker}")
                
            except Exception as e:
                logger.error(f"Error fetching data for ticker {ticker}: {str(e)}")
        
        return all_data
        
    except Exception as e:
        logger.error(f"Error in fetch_market_data: {str(e)}")
        return {}

def fetch_options_data():
    """
    Récupère les données d'options pour tous les tickers et calcule le Gamma Exposure
    """
    try:
        logger.info("Fetching options data...")
        
        for ticker in ALL_TICKERS:
            try:
                # Récupérer le prix actuel
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('regularMarketPrice', None)
                
                if not current_price:
                    logger.warning(f"Could not get price for {ticker}, skipping options data")
                    continue
                
                # Récupérer les chaînes d'options
                expirations = stock.options
                
                if not expirations:
                    logger.warning(f"No options data available for {ticker}")
                    continue
                
                # Prendre les 3 premières dates d'expiration pour le MVP
                all_options = {'calls': [], 'puts': []}
                
                for expiration in expirations[:3]:
                    try:
                        opt = stock.option_chain(expiration)
                        
                        # Traitement des calls
                        calls = opt.calls
                        for _, row in calls.iterrows():
                            all_options['calls'].append({
                                'strike': float(row['strike']),
                                'expiration': expiration,
                                'lastPrice': float(row['lastPrice']),
                                'bid': float(row['bid']),
                                'ask': float(row['ask']),
                                'impliedVolatility': float(row['impliedVolatility']),
                                'openInterest': int(row['openInterest']),
                                'volume': int(row['volume'])
                            })
                        
                        # Traitement des puts
                        puts = opt.puts
                        for _, row in puts.iterrows():
                            all_options['puts'].append({
                                'strike': float(row['strike']),
                                'expiration': expiration,
                                'lastPrice': float(row['lastPrice']),
                                'bid': float(row['bid']),
                                'ask': float(row['ask']),
                                'impliedVolatility': float(row['impliedVolatility']),
                                'openInterest': int(row['openInterest']),
                                'volume': int(row['volume'])
                            })
                    
                    except Exception as e:
                        logger.error(f"Error processing expiration {expiration} for {ticker}: {str(e)}")
                
                # Stocker les données d'options
                options_data_collection.update_one(
                    {'ticker': ticker},
                    {'$set': {
                        'ticker': ticker,
                        'timestamp': datetime.now(),
                        'options': all_options
                    }},
                    upsert=True
                )
                
                # Calculer et stocker le Gamma Exposure
                gamma_analysis = calculate_gamma(all_options, current_price)
                
                gamma_analysis_collection.update_one(
                    {'ticker': ticker},
                    {'$set': {
                        'ticker': ticker,
                        'timestamp': datetime.now(),
                        'spotPrice': current_price,
                        'netGamma': gamma_analysis['netGamma'],
                        'gammaByStrike': gamma_analysis['gammaByStrike'],
                        'gammaLevels': gamma_analysis['gammaLevels']
                    }},
                    upsert=True
                )
                
                logger.info(f"Updated options and gamma data for {ticker}")
                
            except Exception as e:
                logger.error(f"Error processing options for ticker {ticker}: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in fetch_options_data: {str(e)}")
        return False

def generate_trading_strategy(ticker):
    """
    Génère une stratégie de trading basée sur l'analyse du Gamma Exposure
    """
    try:
        # Récupérer les données de marché et de gamma
        market_data = market_data_collection.find_one({'ticker': ticker})
        gamma_data = gamma_analysis_collection.find_one({'ticker': ticker})
        
        if not market_data or not gamma_data:
            return {'error': 'Data not available for this ticker'}
        
        current_price = market_data['close']
        net_gamma = gamma_data['netGamma']
        gamma_levels = gamma_data.get('gammaLevels', [])
        
        # Déterminer la direction du biais en fonction du gamma net
        if net_gamma > 0:
            bias = "bullish"  # Gamma positif = biais haussier
            message = "Le gamma net positif suggère une force haussière et une résistance à la baisse."
        elif net_gamma < 0:
            bias = "bearish"  # Gamma négatif = biais baissier
            message = "Le gamma net négatif suggère une force baissière et une résistance à la hausse."
        else:
            bias = "neutral"
            message = "Le gamma net proche de zéro suggère un marché équilibré sans biais directionnel fort."
        
        # Identifier les niveaux de gamma proches
        nearby_levels = []
        support_levels = []
        resistance_levels = []
        
        for level in gamma_levels:
            strike = level['strike']
            gamma_exposure = level['gammaExposure']
            distance = ((strike / current_price) - 1) * 100  # Distance en pourcentage
            
            if abs(distance) < 5:  # Niveaux à moins de 5% du prix actuel
                nearby_levels.append({
                    'strike': strike,
                    'gammaExposure': gamma_exposure,
                    'distance': distance
                })
            
            # Les niveaux avec gamma positif agissent comme support, négatif comme résistance
            if gamma_exposure > 0 and strike < current_price:
                support_levels.append({
                    'strike': strike,
                    'gammaExposure': gamma_exposure,
                    'distance': distance
                })
            elif gamma_exposure < 0 and strike > current_price:
                resistance_levels.append({
                    'strike': strike,
                    'gammaExposure': gamma_exposure,
                    'distance': distance
                })
        
        # Trier les niveaux
        support_levels = sorted(support_levels, key=lambda x: x['strike'], reverse=True)
        resistance_levels = sorted(resistance_levels, key=lambda x: x['strike'])
        
        # Générer des recommandations
        recommendations = []
        
        if bias == "bullish":
            recommendations.append("Considérer des positions longues avec des stops sous les niveaux de support majeurs.")
            if support_levels:
                closest_support = support_levels[0]['strike']
                recommendations.append(f"Stop suggéré à {closest_support} (support gamma).")
            if resistance_levels:
                closest_resistance = resistance_levels[0]['strike']
                recommendations.append(f"Objectif de profit initial à {closest_resistance} (résistance gamma).")
        
        elif bias == "bearish":
            recommendations.append("Considérer des positions courtes avec des stops au-dessus des niveaux de résistance majeurs.")
            if resistance_levels:
                closest_resistance = resistance_levels[0]['strike']
                recommendations.append(f"Stop suggéré à {closest_resistance} (résistance gamma).")
            if support_levels:
                closest_support = support_levels[0]['strike']
                recommendations.append(f"Objectif de profit initial à {closest_support} (support gamma).")
        
        else:
            recommendations.append("Marché sans biais directionnel clair. Privilégier des stratégies neutres ou attendre une clarification du biais.")
        
        # Structurer la stratégie
        strategy = {
            'ticker': ticker,
            'currentPrice': current_price,
            'timestamp': datetime.now(),
            'bias': bias,
            'netGamma': net_gamma,
            'message': message,
            'nearbyLevels': nearby_levels,
            'supportLevels': support_levels,
            'resistanceLevels': resistance_levels,
            'recommendations': recommendations
        }
        
        return strategy
        
    except Exception as e:
        logger.error(f"Error generating trading strategy for {ticker}: {str(e)}")
        return {'error': str(e)}

# Routes API

@app.route('/api/market-data', methods=['GET'])
def get_market_data():
    """API pour obtenir les données de marché pour tous les tickers"""
    try:
        data = list(market_data_collection.find({}, {'_id': 0}))
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data/<ticker>', methods=['GET'])
def get_ticker_market_data(ticker):
    """API pour obtenir les données de marché pour un ticker spécifique"""
    try:
        data = market_data_collection.find_one({'ticker': ticker}, {'_id': 0})
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'Ticker not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching market data for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamma-data', methods=['GET'])
def get_gamma_data():
    """API pour obtenir les données de gamma pour tous les tickers"""
    try:
        data = list(gamma_analysis_collection.find({}, {'_id': 0}))
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching gamma data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamma-data/<ticker>', methods=['GET'])
def get_ticker_gamma_data(ticker):
    """API pour obtenir les données de gamma pour un ticker spécifique"""
    try:
        data = gamma_analysis_collection.find_one({'ticker': ticker}, {'_id': 0})
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'Ticker not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching gamma data for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading-strategy/<ticker>', methods=['GET'])
def get_trading_strategy(ticker):
    """API pour obtenir la stratégie de trading pour un ticker spécifique"""
    try:
        strategy = generate_trading_strategy(ticker)
        return jsonify(strategy)
    except Exception as e:
        logger.error(f"Error generating trading strategy for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-data', methods=['POST'])
def refresh_data():
    """API pour forcer le rafraîchissement des données"""
    try:
        market_data = fetch_market_data()
        options_data = fetch_options_data()
        
        return jsonify({
            'success': True,
            'marketDataUpdated': bool(market_data),
            'optionsDataUpdated': options_data
        })
    except Exception as e:
        logger.error(f"Error refreshing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Planificateur de tâches
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_market_data, 'interval', minutes=15)
scheduler.add_job(fetch_options_data, 'interval', minutes=30)

# Point d'entrée principal
if __name__ == '__main__':
    # Démarrer le planificateur
    scheduler.start()
    
    # Initialiser les données au démarrage
    fetch_market_data()
    fetch_options_data()
    
    # Démarrer l'application Flask
    app.run(debug=True, host='0.0.0.0', port=5000)