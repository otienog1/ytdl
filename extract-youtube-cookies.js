#!/usr/bin/env node

/**
 * YouTube Cookie Extractor using Puppeteer
 *
 * This script opens a headless browser, navigates to YouTube,
 * waits for you to log in, then extracts and saves cookies
 * in Netscape format for yt-dlp to use.
 *
 * Usage:
 *   node extract-youtube-cookies.js
 *
 * The script will:
 * 1. Open YouTube in a browser
 * 2. Wait for you to log in manually
 * 3. Save cookies to youtube_cookies.txt
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const COOKIE_FILE = path.join(__dirname, 'youtube_cookies.txt');
const YOUTUBE_URL = 'https://www.youtube.com';

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

async function extractCookies() {
  log('\n' + '='.repeat(70), colors.blue);
  log('  YouTube Cookie Extractor', colors.blue);
  log('='.repeat(70) + '\n', colors.blue);

  let browser;

  try {
    // Launch browser
    log('Launching browser...', colors.yellow);
    browser = await puppeteer.launch({
      headless: false, // Show browser so user can log in
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
      ],
      defaultViewport: {
        width: 1280,
        height: 800,
      },
    });

    const page = await browser.newPage();

    // Navigate to YouTube
    log(`Navigating to ${YOUTUBE_URL}...`, colors.yellow);
    await page.goto(YOUTUBE_URL, { waitUntil: 'networkidle2' });

    log('\n' + '='.repeat(70), colors.green);
    log('  ACTION REQUIRED: Please log in to YouTube', colors.green);
    log('='.repeat(70), colors.green);
    log('\nSteps:', colors.yellow);
    log('1. A browser window has opened', colors.yellow);
    log('2. Click "Sign In" in the top right', colors.yellow);
    log('3. Log in with your Google account', colors.yellow);
    log('4. Wait for YouTube homepage to load completely', colors.yellow);
    log('5. Come back here and press ENTER when done\n', colors.yellow);

    // Wait for user input
    await new Promise((resolve) => {
      const readline = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout,
      });

      readline.question('Press ENTER after you have logged in: ', () => {
        readline.close();
        resolve();
      });
    });

    log('\nExtracting cookies...', colors.yellow);

    // Get cookies from the browser
    const cookies = await page.cookies();

    if (cookies.length === 0) {
      throw new Error('No cookies found! Make sure you logged in.');
    }

    // Filter YouTube cookies
    const youtubeCookies = cookies.filter(cookie =>
      cookie.domain.includes('youtube.com') ||
      cookie.domain.includes('google.com')
    );

    if (youtubeCookies.length === 0) {
      throw new Error('No YouTube cookies found! Make sure you logged in to YouTube.');
    }

    log(`Found ${youtubeCookies.length} YouTube cookies`, colors.green);

    // Convert to Netscape format
    const netscapeCookies = convertToNetscapeFormat(youtubeCookies);

    // Save to file
    fs.writeFileSync(COOKIE_FILE, netscapeCookies);

    log('\n' + '='.repeat(70), colors.green);
    log('  SUCCESS! Cookies saved successfully', colors.green);
    log('='.repeat(70), colors.green);
    log(`\nCookie file: ${COOKIE_FILE}`, colors.blue);
    log(`Total cookies: ${youtubeCookies.length}`, colors.blue);

    // Show important cookies
    const importantCookies = ['SSID', 'APISID', 'SAPISID', 'LOGIN_INFO', '__Secure-1PSID'];
    const foundImportant = youtubeCookies.filter(c => importantCookies.includes(c.name));

    if (foundImportant.length > 0) {
      log(`\nImportant cookies found: ${foundImportant.map(c => c.name).join(', ')}`, colors.green);
    } else {
      log('\nWarning: Some important auth cookies may be missing', colors.yellow);
    }

    log('\nNext steps:', colors.blue);
    log('1. The cookie file has been saved automatically', colors.yellow);
    log('2. Restart the worker: sudo systemctl restart ytd-worker', colors.yellow);
    log('3. Try downloading a YouTube Short', colors.yellow);
    log('\nNote: Cookies may expire after 30-90 days. Re-run this script if needed.\n', colors.yellow);

  } catch (error) {
    log('\n' + '='.repeat(70), colors.red);
    log('  ERROR: Failed to extract cookies', colors.red);
    log('='.repeat(70), colors.red);
    log(`\n${error.message}\n`, colors.red);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
      log('Browser closed\n', colors.yellow);
    }
  }
}

/**
 * Convert Puppeteer cookies to Netscape format
 * Format: domain, flag, path, secure, expiration, name, value
 */
function convertToNetscapeFormat(cookies) {
  const header = '# Netscape HTTP Cookie File\n# This file is generated by Puppeteer. Do not edit.\n\n';

  const lines = cookies.map(cookie => {
    const domain = cookie.domain.startsWith('.') ? cookie.domain : '.' + cookie.domain;
    const flag = 'TRUE'; // Domain flag
    const path = cookie.path || '/';
    const secure = cookie.secure ? 'TRUE' : 'FALSE';
    const expiration = cookie.expires ? Math.floor(cookie.expires) : '0';
    const name = cookie.name;
    const value = cookie.value;

    return `${domain}\t${flag}\t${path}\t${secure}\t${expiration}\t${name}\t${value}`;
  });

  return header + lines.join('\n') + '\n';
}

// Run the extractor
extractCookies().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
