/**
 * Simple Express server to serve the reference client
 */
const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from public directory
app.use(express.static('public'));

// Root route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n✅ AI Aikido Gateway - Reference Client`);
  console.log(`🌐 Running on: http://localhost:${PORT}`);
  console.log(`📡 Gateway endpoint: http://localhost:8000`);
  console.log(`\nPress Ctrl+C to stop\n`);
});
