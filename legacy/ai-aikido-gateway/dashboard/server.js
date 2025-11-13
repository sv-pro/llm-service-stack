/**
 * AI Aikido Gateway - Unified Dashboard Server
 * Serves the React dashboard and provides API endpoints
 */

const express = require('express');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'AI Aikido Dashboard',
    version: '0.1.0',
    timestamp: new Date().toISOString()
  });
});

// Serve static files from the dist directory (production)
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'dist')));
  
  // Handle React routing - serve index.html for all routes
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  });
}

// Start server
app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════╗
║  🥋 AI Aikido Gateway - Unified Dashboard     ║
╠════════════════════════════════════════════════╣
║  Dashboard: http://localhost:${PORT}            ║
║  Status:    Server running                     ║
║  Mode:      ${process.env.NODE_ENV || 'development'}                    ║
╚════════════════════════════════════════════════╝
  `);
});
