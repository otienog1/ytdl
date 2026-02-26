# Google Analytics Setup Guide

Google Analytics integration has been added to your YouTube Shorts downloader application. Follow these steps to complete the setup.

## Step 1: Create a Google Analytics Property

If you don't already have a Google Analytics account:

1. Go to [Google Analytics](https://analytics.google.com/)
2. Sign in with your Google account
3. Click "Start measuring"
4. Enter an Account Name (e.g., "YouTube Shorts Downloader")
5. Configure data sharing settings (optional)
6. Click "Next"
7. Create a Property:
   - Property name: "YT Shorts Downloader"
   - Time zone: Select your timezone
   - Currency: Select your currency
8. Click "Next"
9. Select "Create a property only" (skip business details if not applicable)
10. Accept the Terms of Service

## Step 2: Set Up a Data Stream

1. Select "Web" as the platform
2. Enter your website details:
   - Website URL: `https://ytshortsdownload.vercel.app`
   - Stream name: "YT Shorts Downloader Main Site"
3. Click "Create stream"
4. You'll see your **Measurement ID** (format: `G-XXXXXXXXXX`)
5. **Copy this Measurement ID** - you'll need it in the next step

## Step 3: Add Measurement ID to Vercel

### Option A: Through Vercel Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (ytd frontend)
3. Go to "Settings" → "Environment Variables"
4. Add a new variable:
   - **Name**: `NEXT_PUBLIC_GA_ID`
   - **Value**: Your Measurement ID (e.g., `G-XXXXXXXXXX`)
   - **Environments**: Select all (Production, Preview, Development)
5. Click "Save"
6. Redeploy your application:
   - Go to "Deployments" tab
   - Click the three dots on the latest deployment
   - Click "Redeploy"

### Option B: Local Development

1. In the `frontend` directory, create a `.env.local` file:
   ```bash
   cd frontend
   cp .env.local.example .env.local
   ```

2. Edit `.env.local` and add your Measurement ID:
   ```
   NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
   ```

3. Restart your development server

## Step 4: Verify Installation

After deploying with your Measurement ID:

1. Visit your website: `https://ytshortsdownload.vercel.app`
2. Open browser DevTools (F12)
3. Go to the "Network" tab
4. Look for requests to `google-analytics.com/g/collect`
5. If you see these requests, Analytics is working!

### Alternative: Real-Time Reports

1. Go to Google Analytics
2. Click "Reports" → "Realtime"
3. Visit your website in another tab
4. You should see yourself as an active user in the Realtime report

## Step 5: Configure Enhanced Measurement (Optional)

In Google Analytics:

1. Go to Admin → Data Streams → Select your web stream
2. Click "Enhanced measurement"
3. Enable tracking for:
   - Page views (enabled by default)
   - Scrolls
   - Outbound clicks
   - Site search
   - Video engagement
   - File downloads

## What Gets Tracked

The implementation automatically tracks:

- **Page views**: Every page visit
- **User sessions**: Visitor sessions and engagement
- **Traffic sources**: Where visitors come from
- **Device types**: Desktop, mobile, tablet
- **Geographic data**: Country, city (anonymized)
- **Browser and OS**: What browsers and operating systems users use

## Privacy Considerations

The implementation:
- ✅ Only loads when a valid Measurement ID is provided
- ✅ Respects user privacy settings
- ✅ Doesn't track personal information
- ✅ Uses Google's standard analytics tracking

## Viewing Your Data

Access your analytics at: [Google Analytics Dashboard](https://analytics.google.com/)

### Key Reports to Check:

1. **Realtime**: See current visitors
2. **Acquisition**: How users find your site
3. **Engagement**: What pages users visit
4. **Demographics**: User age, gender, interests
5. **Technology**: Devices, browsers, operating systems

## Troubleshooting

### Analytics Not Working?

1. **Check Measurement ID**: Verify it's in format `G-XXXXXXXXXX`
2. **Check Environment Variable**: Make sure `NEXT_PUBLIC_GA_ID` is set in Vercel
3. **Redeploy**: After adding env variable, you must redeploy
4. **Check Browser Console**: Look for any JavaScript errors
5. **Ad Blockers**: Disable ad blockers and try again

### No Data in Reports?

- Wait 24-48 hours for data to appear in standard reports
- Use Realtime reports to see immediate data
- Make sure you're looking at the correct date range

## Next Steps

After setup:

1. Set up **Goals** to track conversions (video downloads)
2. Create **Custom Events** for specific actions
3. Set up **Audiences** for remarketing
4. Link to **Google Search Console** for search data
5. Create **Custom Reports** for your specific metrics

## Files Modified

- `frontend/components/GoogleAnalytics.tsx` - Analytics component
- `frontend/app/layout.tsx` - Integrated Analytics into layout
- `frontend/.env.local.example` - Example environment file

## Support

If you need help:
- [Google Analytics Help Center](https://support.google.com/analytics/)
- [Next.js Analytics Documentation](https://nextjs.org/docs/app/building-your-application/optimizing/analytics)
