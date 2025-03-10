import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import AssetsList from './components/AssetsList';
import AssetDetail from './components/AssetDetail';
import TradingPlan from './components/TradingPlan';
import Dashboard from './components/Dashboard';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

function App() {
  const [loading, setLoading] = useState(true);
  const [assets, setAssets] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMarketData();
    
    // Refresh data every 5 minutes
    const intervalId = setInterval(fetchMarketData, 5 * 60 * 1000);
    
    return () => clearInterval(intervalId);
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/market-data`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setAssets(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching market data:', err);
      setError('Failed to load market data. Please try again later.');
      toast.error('Failed to load market data');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      setLoading(true);
      toast.info('Refreshing market data...');
      
      const response = await fetch(`${API_BASE_URL}/refresh-data`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        await fetchMarketData();
        toast.success('Market data refreshed successfully');
      } else {
        throw new Error('Failed to refresh data');
      }
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError('Failed to refresh market data. Please try again later.');
      toast.error('Failed to refresh market data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Router>
      <div className="app">
        <Navigation />
        
        <div className="main-content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/assets" element={<AssetsList />} />
            <Route path="/asset/:ticker" element={<AssetDetail />} />
            <Route path="/trading-plan/:ticker" element={<TradingPlan />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
        
        <ToastContainer position="bottom-right" />
      </div>
    </Router>
  );
}

export default App;