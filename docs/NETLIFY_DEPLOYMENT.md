# Netlify Deployment Guide — Connect-4 AI & Algorithm Analysis Platform

This guide outlines how to deploy the Connect-4 Flask application live to [Netlify](https://www.netlify.com/) using Netlify Serverless Functions and edge static asset caching.

---

## Architecture Overview

```
                      ┌───────────────────────────────────────┐
                      │              User Browser             │
                      └──────────────────┬────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      [Static Assets: /static/*]                  [Dynamic Routes: /*]
      Served directly by Netlify CDN              Redirected to Netlify Function
      (CSS, JavaScript, Icons)                    (netlify/functions/app.py)
                   │                                           │
                   ▼                                           ▼
          High-Speed Global Edge                      Flask 3.1 Python Engine
                                                    (Minimax, Alpha-Beta, TT, Game)
```

1. **Static Assets:** CSS and JavaScript (`static/css/style.css`, `static/js/game.js`, `static/js/dashboard.js`) are published to the edge CDN and served with long-term caching.
2. **Serverless Backend:** Dynamic requests (`/`, `/api/state`, `/api/move`, `/api/ai-move`, `/api/reset`, `/api/benchmark/*`) are handled by `netlify/functions/app.py`, which bridges AWS Lambda/Netlify API Gateway events to the authoritative Python Flask application.
3. **Configuration:** Automated via [`netlify.toml`](../netlify.toml) and [`runtime.txt`](../runtime.txt).

---

## Step-by-Step Deployment Instructions

### Method 1: Connecting Netlify to GitHub (Recommended)

1. **Log in to Netlify:**
   Visit [app.netlify.com](https://app.netlify.com/) and sign in with your GitHub account.

2. **Add New Site:**
   - On your Netlify dashboard, click the **"Add new site"** button.
   - Select **"Import an existing project"**.

3. **Authorize and Select Repository:**
   - Choose **GitHub** as your Git provider.
   - In the repository search bar, select:
     ```
     Shaunak-Rahatekar/CONNECT-4
     ```

4. **Verify Build Settings:**
   Netlify will automatically detect the settings from [`netlify.toml`](../netlify.toml):
   - **Branch to deploy:** `main`
   - **Build command:** `mkdir -p public/static && cp -r static/* public/static/ && pip install -r requirements.txt`
   - **Publish directory:** `public`
   - **Functions directory:** `netlify/functions`

5. **Deploy the Site:**
   - Click **"Deploy CONNECT-4"**.
   - Netlify will clone the repository, install Python dependencies, configure the serverless function, and provision your live URL (e.g., `https://connect4-daa.netlify.app`).

---

### Method 2: Deploying via Netlify CLI (Optional)

If you have the [Netlify CLI](https://docs.netlify.com/cli/get-started/) installed:

```powershell
# 1. Log in to your Netlify account:
netlify login

# 2. Initialize and link the site:
netlify init

# 3. Deploy to production:
netlify deploy --prod
```

---

## Verifying the Live Deployment

Once the build finishes in your Netlify dashboard:

1. **Visit the Live URL:** Open `https://<your-site-name>.netlify.app` in your browser.
2. **Test Gameplay:**
   - Drop a disc into any column.
   - Switch mode to **Play vs AI** and verify that Alpha-Beta Pruning computes moves.
3. **Test Benchmarks:**
   - Scroll down to the **AI Performance & Benchmark Dashboard**.
   - Click **▶ Run Benchmark Suite** and verify that the comparison table and Chart.js graphs render.
4. **Health Check Endpoint:**
   - Visit `https://<your-site-name>.netlify.app/api/status` to verify the JSON status response:
     ```json
     {
       "status": "ok",
       "application": "Connect-4 DAA",
       "python_game_engine": "active"
     }
     ```

---

## Troubleshooting

- **Function Timeout:** Netlify free-tier serverless functions have a 10-second execution timeout. Searches up to depth $d=4$ execute in under 400 ms, well within this limit.
- **Cache Persistence:** Netlify serverless functions run in ephemeral container instances. Match sessions remain active during consecutive plays, but if a cold container spins down, clicking **⟳ New Game** cleanly re-initializes the state.
