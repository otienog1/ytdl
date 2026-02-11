#!/usr/bin/env node

/**
 * YouTube Cookie Extractor - Standalone Tool
 *
 * Extracts YouTube authentication cookies using Puppeteer for use with yt-dlp.
 * This is a completely standalone tool that can be used with any yt-dlp project.
 *
 * Usage:
 *   npm install                                    # Install dependencies
 *   node extract-youtube-cookies.js                # Extract to youtube_cookies.txt
 *   node extract-youtube-cookies.js -o cookies.txt # Custom output file
 *   node extract-youtube-cookies.js --help         # Show help
 *
 * Author: YouTube Downloader Team
 * License: MIT
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const helpFlag = args.includes('--help') || args.includes('-h');
const outputIndex = args.indexOf('--output') !== -1 ? args.indexOf('--output') : args.indexOf('-o');
const outputFile = outputIndex !== -1 ? args[outputIndex + 1] : 'youtube_cookies.txt';
const COOKIE_FILE = path.resolve(outputFile);
const YOUTUBE_URL = 'https://www.youtube.com';

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function showHelp() {
  console.log(`
${colors.bold}${colors.cyan}YouTube Cookie Extractor${colors.reset}
${colors.yellow}A standalone tool to extract YouTube cookies for yt-dlp${colors.reset}

${colors.bold}USAGE:${colors.reset}
  node extract-youtube-cookies.js [OPTIONS]

${colors.bold}OPTIONS:${colors.reset}
  -o, --output <file>    Output file path (default: youtube_cookies.txt)
  -h, --help            Show this help message

${colors.bold}EXAMPLES:${colors.reset}
  ${colors.cyan}# Extract cookies to default file${colors.reset}
  node extract-youtube-cookies.js

  ${colors.cyan}# Extract cookies to custom file${colors.reset}
  node extract-youtube-cookies.js -o /path/to/cookies.txt

  ${colors.cyan}# Show help${colors.reset}
  node extract-youtube-cookies.js --help

${colors.bold}HOW IT WORKS:${colors.reset}
  1. Opens a browser window with YouTube
  2. You manually log in with your Google account
  3. Script extracts all authentication cookies
  4. Saves cookies in Netscape format for yt-dlp

${colors.bold}COOKIE LIFETIME:${colors.reset}
  YouTube cookies typically last 30-90 days. Re-run this script when they expire.

${colors.bold}USE WITH YT-DLP:${colors.reset}
  yt-dlp --cookies youtube_cookies.txt https://youtube.com/shorts/VIDEO_ID

${colors.bold}USE WITH PYTHON:${colors.reset}
  ydl_opts = {
      'cookiefile': 'youtube_cookies.txt',
  }

${colors.bold}SECURITY:${colors.reset}
  - Keep the cookie file secure (contains your authentication)
  - Don't commit to Git (add to .gitignore)
  - Set file permissions: chmod 600 youtube_cookies.txt

${colors.bold}MORE INFO:${colors.reset}
  https://github.com/yt-dlp/yt-dlp#authentication-with-cookies
`);
  process.exit(0);
}

if (helpFlag) {
  showHelp();
}

async function extractCookies() {
  log('\n' + '='.repeat(70), colors.cyan);
  log(`${colors.bold}  YouTube Cookie Extractor - Standalone Tool${colors.reset}`, colors.cyan);
  log('='.repeat(70) + '\n', colors.cyan);

  log(`Output file: ${COOKIE_FILE}`, colors.blue);
  log('');

  let browser;

  try {
    // Launch browser
    log('Launching browser...', colors.yellow);

    // Try to find Chrome executable path
    const getChromePath = () => {
      const platform = process.platform;
      if (platform === 'win32') {
        return 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
      } else if (platform === 'darwin') {
        return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
      } else {
        return '/usr/bin/google-chrome';
      }
    };

    const launchOptions = {
      headless: false, // Show browser so user can log in
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled', // Hide automation
        '--disable-features=IsolateOrigins,site-per-process',
      ],
      ignoreDefaultArgs: ['--enable-automation'], // Remove automation flag
      defaultViewport: {
        width: 1280,
        height: 800,
      },
    };

    // Try to use system Chrome first (has latest features)
    const chromePath = getChromePath();
    if (fs.existsSync(chromePath)) {
      launchOptions.executablePath = chromePath;
      log(`Using system Chrome: ${chromePath}`, colors.cyan);
    } else {
      log('Using bundled Chromium (system Chrome not found)', colors.yellow);
    }

    browser = await puppeteer.launch(launchOptions);

    const page = await browser.newPage();

    // Hide webdriver property and make browser look more legitimate
    await page.evaluateOnNewDocument(() => {
      // Remove webdriver property
      Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
      });

      // Mock plugins to avoid detection
      Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
      });

      // Mock languages
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
      });

      // Override chrome property
      window.chrome = {
        runtime: {},
      };

      // Override permissions
      const originalQuery = window.navigator.permissions.query;
      window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
          Promise.resolve({ state: Notification.permission }) :
          originalQuery(parameters)
      );
    });

    // Set a realistic user agent
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    // Navigate to YouTube
    log(`Navigating to ${YOUTUBE_URL}...`, colors.yellow);
    await page.goto(YOUTUBE_URL, { waitUntil: 'networkidle2' });

    log('\n' + '='.repeat(70), colors.green);
    log(`${colors.bold}  ACTION REQUIRED: Please log in to YouTube${colors.reset}`, colors.green);
    log('='.repeat(70), colors.green);
    log('\nSteps:', colors.bold);
    log('  1. A browser window has opened showing YouTube', colors.yellow);
    log('  2. Click "Sign In" button in the top right corner', colors.yellow);
    log('  3. Log in with your Google account credentials', colors.yellow);
    log('  4. Wait for YouTube homepage to fully load', colors.yellow);
    log('  5. Return here and press ENTER to continue\n', colors.yellow);

    log(`${colors.cyan}Tip: Make sure you're fully logged in before pressing ENTER${colors.reset}\n`);

    // Wait for user input
    await new Promise((resolve) => {
      const readline = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout,
      });

      readline.question(`${colors.bold}Press ENTER after you have logged in: ${colors.reset}`, () => {
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

    // Filter YouTube/Google cookies
    const youtubeCookies = cookies.filter(cookie =>
      cookie.domain.includes('youtube.com') ||
      cookie.domain.includes('google.com')
    );

    if (youtubeCookies.length === 0) {
      throw new Error('No YouTube cookies found! Make sure you logged in to YouTube.');
    }

    log(`✓ Found ${youtubeCookies.length} YouTube/Google cookies`, colors.green);

    // Convert to Netscape format
    const netscapeCookies = convertToNetscapeFormat(youtubeCookies);

    // Save to file
    fs.writeFileSync(COOKIE_FILE, netscapeCookies);

    log('\n' + '='.repeat(70), colors.green);
    log(`${colors.bold}  ✓ SUCCESS! Cookies saved successfully${colors.reset}`, colors.green);
    log('='.repeat(70), colors.green);

    log(`\n${colors.bold}Cookie Details:${colors.reset}`);
    log(`  File: ${COOKIE_FILE}`, colors.blue);
    log(`  Total cookies: ${youtubeCookies.length}`, colors.blue);
    log(`  Format: Netscape (yt-dlp compatible)`, colors.blue);

    // Show important cookies
    const importantCookies = ['SSID', 'APISID', 'SAPISID', 'LOGIN_INFO', '__Secure-1PSID', '__Secure-3PSID'];
    const foundImportant = youtubeCookies.filter(c => importantCookies.includes(c.name));

    if (foundImportant.length > 0) {
      log(`  Auth cookies: ${foundImportant.map(c => c.name).join(', ')}`, colors.green);
    } else {
      log(`  ${colors.yellow}Warning: Some important auth cookies may be missing${colors.reset}`);
    }

    log(`\n${colors.bold}Next Steps:${colors.reset}`);
    log(`  ${colors.cyan}1. Use with yt-dlp:${colors.reset}`);
    log(`     yt-dlp --cookies ${path.basename(COOKIE_FILE)} https://youtube.com/shorts/VIDEO_ID`);
    log(`\n  ${colors.cyan}2. Use with Python/yt-dlp:${colors.reset}`);
    log(`     ydl_opts = {'cookiefile': '${path.basename(COOKIE_FILE)}'}`);
    log(`\n  ${colors.cyan}3. Secure the file:${colors.reset}`);
    log(`     chmod 600 ${path.basename(COOKIE_FILE)}  # On Linux/Mac`);

    log(`\n${colors.yellow}Note: Cookies expire after 30-90 days. Re-run this script when needed.${colors.reset}\n`);

  } catch (error) {
    log('\n' + '='.repeat(70), colors.red);
    log(`${colors.bold}  ✗ ERROR: Failed to extract cookies${colors.reset}`, colors.red);
    log('='.repeat(70), colors.red);
    log(`\n${error.message}`, colors.red);
    log(`\n${colors.yellow}Troubleshooting:${colors.reset}`);
    log(`  - Make sure you actually logged in to YouTube`);
    log(`  - Wait for the page to fully load before pressing ENTER`);
    log(`  - Try running the script again`);
    log(`  - Check if Puppeteer/Chromium is installed correctly\n`);
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
  const header = '# Netscape HTTP Cookie File\n# This file is generated by YouTube Cookie Extractor\n# https://github.com/yt-dlp/yt-dlp#authentication-with-cookies\n\n';

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
