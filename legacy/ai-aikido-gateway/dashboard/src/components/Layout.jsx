import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import './Layout.css';

function Layout() {
  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <h1>🥋 AI Aikido</h1>
          <p className="subtitle">Gateway Dashboard</p>
        </div>
        
        <div className="nav-links">
          <NavLink to="/playground" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">🎮</span>
            <span>Playground</span>
          </NavLink>

          <NavLink to="/rere-demo" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">🔄</span>
            <span>Re^Re Loop Demo</span>
          </NavLink>

          <NavLink to="/overview" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">📊</span>
            <span>Overview</span>
          </NavLink>

          <NavLink to="/costs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">💰</span>
            <span>Cost Explorer</span>
          </NavLink>

          <NavLink to="/requests" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">📋</span>
            <span>Request History</span>
          </NavLink>

          <NavLink to="/cache" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">⚡</span>
            <span>Cache Analytics</span>
          </NavLink>

          <NavLink to="/settings" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <span className="icon">⚙️</span>
            <span>Settings</span>
          </NavLink>
        </div>
        
        <div className="sidebar-footer">
          <div className="status-indicator">
            <span className="status-dot online"></span>
            <span>Gateway Online</span>
          </div>
        </div>
      </nav>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
