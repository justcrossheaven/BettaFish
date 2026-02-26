import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import os from 'os';

(async () => {
    let browser;

    try {
        // Use a persistent context with a real Chrome user data directory
        // This makes it look like a real browser to Google
        const userDataDir = path.join(os.tmpdir(), 'playwright-twitter-auth');

        console.log('Launching browser with persistent context...');
        console.log(`User data directory: ${userDataDir}`);

        // Launch with channel: 'chrome' to use your installed Chrome instead of Chromium
        const context = await chromium.launchPersistentContext(userDataDir, {
            headless: false,
            channel: 'chrome', // Use your installed Chrome browser
            viewport: { width: 1280, height: 720 },
            args: [
                '--disable-blink-features=AutomationControlled', // Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        });

        const page = context.pages()[0] || await context.newPage();

        console.log('\nOpening Twitter/X...');
        await page.goto('https://twitter.com', {
            waitUntil: 'domcontentloaded', // More reliable than networkidle for Twitter
            timeout: 60000 // 60 second timeout
        });

        console.log('\n' + '='.repeat(60));
        console.log('PLEASE LOG IN TO TWITTER/X');
        console.log('='.repeat(60));
        console.log('\nInstructions:');
        console.log('1. Complete the login process (Google Sign-In should work now!)');
        console.log('2. Wait until you see your home timeline');
        console.log('3. DO NOT close the browser - the script will auto-save and close');
        console.log('\nWaiting for successful login...');
        console.log('(Timeout: 5 minutes)\n');

        // Wait for successful login by detecting home timeline or user menu
        try {
            await page.waitForSelector('[data-testid="AppTabBar_Home_Link"], [data-testid="SideNav_NewTweet_Button"], [aria-label="Home timeline"]', {
                timeout: 300000 // 5 minutes - more time for Google OAuth flow
            });
            console.log('\n✓ Login detected successfully!');
        } catch (timeoutError) {
            console.log('\n⚠ Timeout waiting for login. Saving cookies anyway...');
        }

        // Small delay to ensure all cookies are set
        await page.waitForTimeout(2000);

        console.log('\nSaving storage state (cookies and localStorage)...');
        const state = await context.storageState();

        // Save to twitter_cookies.json (matches the .env TWITTER_COOKIES_PATH)
        const cookiesPath = 'twitter_cookies.json';
        fs.writeFileSync(cookiesPath, JSON.stringify(state, null, 2));

        console.log(`\n✓ Cookies saved to ${cookiesPath}`);
        console.log('\nStorage state includes:');
        console.log(`  - ${state.cookies.length} cookies`);
        console.log(`  - ${state.origins.length} localStorage entries`);

        // Verify auth_token is present
        const hasAuthToken = state.cookies.some(c => c.name === 'auth_token');
        if (hasAuthToken) {
            console.log('\n✓ auth_token found - login successful!');
        } else {
            console.log('\n⚠ WARNING: auth_token not found - you may need to log in again');
        }

        await context.close();
        console.log('\n✓ Browser closed. You can now use these cookies in your application.\n');

    } catch (error) {
        if (error.message.includes('Target page, context or browser has been closed')) {
            console.error('\n✗ ERROR: Browser was closed manually before cookies could be saved.');
            console.error('Please run the script again and keep the browser open until it saves automatically.\n');
        } else {
            console.error('\n✗ ERROR:', error.message);
            console.error('\nIf you see "Executable doesn\'t exist", try removing channel: \'chrome\' from the script.\n');
        }
        process.exit(1);
    }
})();
