import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaArrowUp, FaArrowDown, FaSpinner, FaSync } from 'react-icons/fa';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

const Dashboard = () => {
  const [marketData, setMarketData] = useState([]);
  const [gammaData, setGammaData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const [marketDataResponse, gammaDataResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/market-data`),
        fetch(`${API_BASE_URL}/gamma-data`)
      ]);
      
      if (!marketDataResponse.ok || !gammaDataResponse.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      
      const marketData = await marketDataResponse.json();
      const gammaData = await gammaDataResponse.json();
      
      setMarketData(marketData);
      setGammaData(gammaData);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      
      const response = await fetch(`${API_BASE_URL}/refresh-data`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh data');
      }
      
      await fetchDashboardData();
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError('Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  const getGammaForTicker = (ticker) => {
    const tickerData = gammaData.find(item => item.ticker === ticker);
    return tickerData ? tickerData.netGamma : null;
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleTimeString();
  };

  const GammaSummaryChart = ({ gammaData }) => {
    // Préparer les données pour le graphique
    const chartData = gammaData.map(item => ({
      name: item.ticker.startsWith('^') 
        ? item.ticker === '^GSPC' 
          ? 'S&P 500' 
          : item.ticker === '^NDX' 
          ? 'Nasdaq 100' 
          : item.ticker === '^DJI' 
          ? 'Dow Jones' 
          : item.ticker
        : item.ticker,
      gamma: item.netGamma || 0
    }));
  
    return (
      <div className="gamma-chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end"
              height={70}
            />
            <YAxis label={{ value: 'Gamma Net', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => value.toFixed(2)} />
            <Legend />
            <Bar 
              dataKey="gamma" 
              name="Gamma Exposure" 
              fill={(entry) => entry.gamma >= 0 ? "#4CAF50" : "#F44336"}
              isAnimationActive={true}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="dashboard loading">
        <FaSpinner className="spinner" />
        <p>Chargement des données...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard error">
        <h2>Erreur</h2>
        <p>{error}</p>
        <button onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? <FaSpinner className="spinner" /> : <FaSync />} Réessayer
        </button>
      </div>
    );
  }

  // Organiser les données par catégorie (indices et actions)
  const indices = marketData.filter(asset => asset.ticker.startsWith('^'));
  const stocks = marketData.filter(asset => !asset.ticker.startsWith('^'));

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Tableau de bord - Gamma Exposure</h1>
        <button 
          className="refresh-button" 
          onClick={handleRefresh} 
          disabled={refreshing}
        >
          {refreshing ? <FaSpinner className="spinner" /> : <FaSync />} 
          {refreshing ? 'Actualisation...' : 'Actualiser les données'}
        </button>
      </div>

      <div className="dashboard-summary">
        <div className="gamma-overview">
          <h2>Aperçu Gamma</h2>
          <GammaSummaryChart gammaData={gammaData} />
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="market-section">
          <h2>Indices de marché</h2>
          <div className="assets-table">
            <table>
              <thead>
                <tr>
                  <th>Indice</th>
                  <th>Prix</th>
                  <th>Variation</th>
                  <th>Gamma Net</th>
                  <th>Dernière mise à jour</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {indices.map(index => {
                  const gamma = getGammaForTicker(index.ticker);
                  const indexName = index.ticker === '^GSPC' 
                    ? 'S&P 500' 
                    : index.ticker === '^NDX' 
                    ? 'Nasdaq 100' 
                    : index.ticker === '^DJI' 
                    ? 'Dow Jones' 
                    : index.ticker;
                  
                  return (
                    <tr key={index.ticker}>
                      <td>{indexName}</td>
                      <td>{index.close.toFixed(2)}</td>
                      <td className={index.change >= 0 ? 'positive' : 'negative'}>
                        {index.change >= 0 ? <FaArrowUp /> : <FaArrowDown />}
                        {Math.abs(index.change).toFixed(2)}%
                      </td>
                      <td className={gamma > 0 ? 'positive' : gamma < 0 ? 'negative' : ''}>
                        {gamma ? gamma.toFixed(2) : 'N/A'}
                      </td>
                      <td>{formatTime(index.timestamp)}</td>
                      <td>
                        <Link to={`/asset/${index.ticker}`} className="view-link">Détails</Link>
                        <Link to={`/trading-plan/${index.ticker}`} className="plan-link">Plan</Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="market-section">
          <h2>Actions principales</h2>
          <div className="assets-table">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Prix</th>
                  <th>Variation</th>
                  <th>Gamma Net</th>
                  <th>Dernière mise à jour</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {stocks.map(stock => {
                  const gamma = getGammaForTicker(stock.ticker);
                  
                  return (
                    <tr key={stock.ticker}>
                      <td>{stock.ticker}</td>
                      <td>{stock.close.toFixed(2)}</td>
                      <td className={stock.change >= 0 ? 'positive' : 'negative'}>
                        {stock.change >= 0 ? <FaArrowUp /> : <FaArrowDown />}
                        {Math.abs(stock.change).toFixed(2)}%
                      </td>
                      <td className={gamma > 0 ? 'positive' : gamma < 0 ? 'negative' : ''}>
                        {gamma ? gamma.toFixed(2) : 'N/A'}
                      </td>
                      <td>{formatTime(stock.timestamp)}</td>
                      <td>
                        <Link to={`/asset/${stock.ticker}`} className="view-link">Détails</Link>
                        <Link to={`/trading-plan/${stock.ticker}`} className="plan-link">Plan</Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;