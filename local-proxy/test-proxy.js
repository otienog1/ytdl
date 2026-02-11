#!/usr/bin/env node

/**
 * Simple test script to verify proxy is working
 * Usage: node test-proxy.js
 */

const net = require('net');

const PORT = 1080;
const HOST = '0.0.0.0';

console.log('\n' + '='.repeat(60));
console.log('Testing if port 1080 is accessible...');
console.log('='.repeat(60) + '\n');

// Create a simple TCP server on port 1080
const server = net.createServer((socket) => {
  const clientInfo = `${socket.remoteAddress}:${socket.remotePort}`;
  console.log(`✓ Connection received from: ${clientInfo}`);

  // Echo back what we receive
  socket.on('data', (data) => {
    console.log(`  Received ${data.length} bytes from ${clientInfo}`);
    console.log(`  Data: ${data.toString('hex').substring(0, 40)}...`);
  });

  socket.on('end', () => {
    console.log(`  Connection closed: ${clientInfo}\n`);
  });

  socket.on('error', (err) => {
    console.log(`  Error from ${clientInfo}: ${err.message}\n`);
  });
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.log('\x1b[31m%s\x1b[0m', '✗ Port 1080 is already in use!');
    console.log('  This is GOOD if your proxy is running.');
    console.log('  This is BAD if nothing is using port 1080.');
    console.log('\n  To check what\'s using the port:');
    console.log('    Windows: netstat -ano | findstr :1080');
    console.log('    Mac/Linux: lsof -i :1080');
  } else {
    console.log('\x1b[31m%s\x1b[0m', `✗ Error: ${err.message}`);
  }
  process.exit(1);
});

server.listen(PORT, HOST, () => {
  console.log('\x1b[32m%s\x1b[0m', `✓ Test server listening on ${HOST}:${PORT}`);
  console.log('\nThis means:');
  console.log('  1. Port 1080 is available (not blocked by firewall locally)');
  console.log('  2. You can run the proxy on this port');
  console.log('\nNext steps:');
  console.log('  1. Press Ctrl+C to stop this test');
  console.log('  2. Run the actual proxy: node simple-proxy.js --port 1080 --auth ytd_user:ytdlPass@12');
  console.log('  3. From another machine, test connection to: 197.237.3.52:1080');
  console.log('\nWaiting for connections... (Press Ctrl+C to stop)\n');
});

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log('\n\n\x1b[33m%s\x1b[0m', '⚠ Stopping test server...');
  server.close(() => {
    console.log('\x1b[32m%s\x1b[0m', '✓ Test server stopped');
    process.exit(0);
  });
});
