import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaChartLine, FaList, FaChartBar, FaTachometerAlt } from 'react-icons/fa';
import '../styles/Navigation.css';

const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="navigation">
      <div className="logo">
        <h1>GammaTracker</h1>
      </div>
      <ul className="nav-links">
        <li className={location.pathname === '/dashboard' ? 'active' : ''}>
          <Link to="/dashboard">
            <FaTachometerAlt /> Dashboard
          </Link>
        </li>
        <li className={location.pathname === '/assets' ? 'active' : ''}>
          <Link to="/assets">
            <FaList /> Liste des actifs
          </Link>
        </li>
        <li className={location.pathname.startsWith('/asset/') ? 'active' : ''}>
          <Link to={location.pathname.startsWith('/asset/') ? location.pathname : '/assets'}>
            <FaChartLine /> Détail de l'actif
          </Link>
        </li>
        <li className={location.pathname.startsWith('/trading-plan/') ? 'active' : ''}>
          <Link to={location.pathname.startsWith('/trading-plan/') ? location.pathname : '/assets'}>
            <FaChartBar /> Plan de trading
          </Link>
        </li>
      </ul>
      <div className="nav-footer">
        <p>© 2025 GammaTracker</p>
      </div>
    </nav>
  );
};

export default Navigation;