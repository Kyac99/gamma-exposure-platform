import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaArrowUp, FaArrowDown, FaSpinner, FaSync, FaSearch } from 'react-icons/fa';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

const AssetsList = () => {
  const [assets, setAssets] = useState([]);
  const [filteredAssets, setFilteredAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [gammaData, setGammaData] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (assets.length > 0) {
      setFilteredAssets(
        assets.filter(asset =>
          asset.ticker.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }
  }, [searchTerm, assets]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [marketDataResponse, gammaDataResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/market-data`),
        fetch(`${API_BASE_URL}/gamma-data`)
      ]);
      
      if (!marketDataResponse.ok || !gammaDataResponse.ok) {
        throw new Error('Failed to fetch data');
      }
      
      const marketData = await marketDataResponse.json();
      const gammaData = await gammaDataResponse.json();
      
      setAssets(marketData);
      setFilteredAssets(marketData);
      setGammaData(gammaData);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data. Please try again later.');
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
      
      await fetchData();
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

  if (loading) {
    return (
      <div className="assets-list loading">
        <FaSpinner className="spinner" />
        <p>Chargement des actifs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assets-list error">
        <h2>Erreur</h2>
        <p>{error}</p>
        <button onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? <FaSpinner className="spinner" /> : <FaSync />} Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="assets-list">
      <div className="assets-header">
        <h1>Liste des actifs</h1>
        <div className="actions">
          <div className="search-bar">
            <FaSearch />
            <input
              type="text"
              placeholder="Rechercher un actif..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button
            className="refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? <FaSpinner className="spinner" /> : <FaSync />}
            {refreshing ? 'Actualisation...' : 'Actualiser'}
          </button>
        </div>
      </div>

      <div className="assets-container">
        <table className="assets-table">
          <thead>
            <tr>
              <th>Symbole</th>
              <th>Nom</th>
              <th>Dernier prix</th>
              <th>Variation</th>
              <th>Volume</th>
              <th>Gamma Net</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAssets.map((asset) => {
              const gamma = getGammaForTicker(asset.ticker);
              const assetName = asset.ticker.startsWith('^') 
                ? asset.ticker === '^GSPC' 
                  ? 'S&P 500' 
                  : asset.ticker === '^NDX' 
                  ? 'Nasdaq 100' 
                  : asset.ticker === '^DJI' 
                  ? 'Dow Jones' 
                  : asset.ticker
                : asset.ticker;
              
              return (
                <tr key={asset.ticker}>
                  <td>{asset.ticker}</td>
                  <td>{assetName}</td>
                  <td>${asset.close.toFixed(2)}</td>
                  <td className={asset.change >= 0 ? 'positive' : 'negative'}>
                    {asset.change >= 0 ? <FaArrowUp /> : <FaArrowDown />}
                    {Math.abs(asset.change).toFixed(2)}%
                  </td>
                  <td>{asset.volume.toLocaleString()}</td>
                  <td className={gamma > 0 ? 'positive' : gamma < 0 ? 'negative' : ''}>
                    {gamma !== null ? gamma.toFixed(2) : 'N/A'}
                  </td>
                  <td className="actions-cell">
                    <Link to={`/asset/${asset.ticker}`} className="view-button">
                      Détails
                    </Link>
                    <Link to={`/trading-plan/${asset.ticker}`} className="plan-button">
                      Plan
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AssetsList;