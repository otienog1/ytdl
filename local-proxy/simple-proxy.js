#!/usr/bin/env node

/**
 * Simple SOCKS5 Proxy Server
 *
 * This creates a residential proxy by running on your local machine
 * and forwarding requests through your home internet connection.
 *
 * Your cloud server will connect to this proxy to bypass YouTube's
 * datacenter IP blocking.
 *
 * Usage:
 *   node simple-proxy.js
 *   node simple-proxy.js --port 1080 --auth user:password
 */

const socks = require('socksv5');
const os = require('os');

// Parse command line arguments
const args = process.argv.slice(2);
let port = 1080;
let username = null;
let password = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--port' && args[i + 1]) {
    port = parseInt(args[i + 1]);
    i++;
  } else if (args[i] === '--auth' && args[i + 1]) {
    const [user, pass] = args[i + 1].split(':');
    username = user;
    password = pass;
    i++;
  }
}

// Get local IP address
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return '127.0.0.1';
}

const localIP = getLocalIP();

// Create SOCKS5 server
const server = socks.createServer((info, accept, deny) => {
  // Accept the connection
  accept();
});

// Add authentication if credentials provided
if (username && password) {
  server.useAuth(socks.auth.UserPassword((user, pass, cb) => {
    cb(user === username && pass === password);
  }));

  console.log('\x1b[32m%s\x1b[0m', '✓ Authentication enabled');
  console.log(`  Username: ${username}`);
  console.log(`  Password: ${'*'.repeat(password.length)}`);
} else {
  server.useAuth(socks.auth.None());
  console.log('\x1b[33m%s\x1b[0m', '⚠ WARNING: No authentication - proxy is open to anyone!');
  console.log('  Use --auth user:password for security');
}

// Start server
server.listen(port, '0.0.0.0', () => {
  console.log('\n' + '='.repeat(60));
  console.log('\x1b[36m%s\x1b[0m', '  SOCKS5 Residential Proxy Server');
  console.log('='.repeat(60));
  console.log('');
  console.log('\x1b[32m%s\x1b[0m', `✓ Server running on port ${port}`);
  console.log('');
  console.log('Local Network:');
  console.log(`  socks5://${username ? `${username}:${password}@` : ''}${localIP}:${port}`);
  console.log('');
  console.log('Localhost:');
  console.log(`  socks5://${username ? `${username}:${password}@` : ''}127.0.0.1:${port}`);
  console.log('');
  console.log('\x1b[33m%s\x1b[0m', 'Next Steps:');
  console.log('  1. Make sure your router forwards port', port, 'to this machine');
  console.log('  2. Get your public IP: curl ifconfig.me');
  console.log('  3. Use this on your server:');
  console.log(`     YT_DLP_PROXY=socks5://${username ? `${username}:${password}@` : ''}YOUR_PUBLIC_IP:${port}`);
  console.log('');
  console.log('='.repeat(60));
  console.log('\nPress Ctrl+C to stop\n');
});

// Handle errors
server.on('error', (err) => {
  console.error('\x1b[31m%s\x1b[0m', '✗ Error:', err.message);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n\x1b[33m%s\x1b[0m', '⚠ Shutting down proxy server...');
  server.close(() => {
    console.log('\x1b[32m%s\x1b[0m', '✓ Server stopped');
    process.exit(0);
  });
});

// Log connections
let connectionCount = 0;
server.on('proxyConnect', (info, destination) => {
  connectionCount++;
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] Connection #${connectionCount}: ${destination.address}:${destination.port}`);
});
