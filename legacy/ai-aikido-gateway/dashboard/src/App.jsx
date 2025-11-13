import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Playground from './pages/Playground';
import Overview from './pages/Overview';
import RequestHistory from './pages/RequestHistory';
import CostExplorer from './pages/CostExplorer';
import CacheAnalytics from './pages/CacheAnalytics';
import Settings from './pages/Settings';
import ReReLoopDemo from './pages/playbooks/ReReLoopDemo';
import './App.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/playground" replace />} />
        <Route path="playground" element={<Playground />} />
        <Route path="rere-demo" element={<ReReLoopDemo />} />
        <Route path="overview" element={<Overview />} />
        <Route path="costs" element={<CostExplorer />} />
        <Route path="requests" element={<RequestHistory />} />
        <Route path="cache" element={<CacheAnalytics />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
