# YouTube Shorts Automation Agent (OpenRouter)

A starter Streamlit project for generating YouTube Shorts scripts with OpenRouter, creating a basic vertical video with narration, and uploading it through the YouTube Data API.

## What it does
- Generates a short script, title, description, and hashtags with an OpenRouter chat model.
- Uses gTTS for narration and FFmpeg/Pillow to create a basic 9:16 title-card video.
- Can upload through YouTube Data API OAuth after you configure Google Cloud credentials.
- Upload defaults to **private**; review the video before publishing.

## Important limitations
- This is a starter project, not a fully unattended trend-research system.
- It does not independently verify live trends; provide a topic or use the idea-generation feature.
- The video is a basic title-card with narration, not a stock-footage montage.
- Uploading is triggered from the app rather than scheduled automatically.
- OpenRouter's free models have usage and provider availability limits. The free tier currently lists 50 requests/day, subject to change.

## 1. Install
Use Python 3.11 or 3.12 and install FFmpeg, then add FFmpeg's `bin` folder to PATH.

In the project folder, open Command Prompt:
```bat
py -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure OpenRouter
1. Create an account at https://openrouter.ai/
2. Create a key at https://openrouter.ai/keys
3. Copy `.env.example` to a new file named `.env`.
4. Put your key in `.env`:
```env
OPENROUTER_API_KEY=your_real_key_here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_SITE_URL=http://localhost:8501
OPENROUTER_APP_NAME=YouTube Shorts Automation Agent
```
`openrouter/free` routes to eligible free models when available. Alternatively choose an active model whose ID ends in `:free` from https://openrouter.ai/models?max_price=0. Do not share your key or commit `.env` to GitHub.

## 3. Configure YouTube upload
1. In Google Cloud Console, create/select a project.
2. Enable YouTube Data API v3.
3. Create OAuth client credentials for a Desktop app and download the JSON file.
4. Save it as `client_secret.json` in this project folder.
5. Start the app and use the upload control. The first OAuth login opens a browser.
6. New/unverified API projects may have upload restrictions; follow Google's current verification/audit requirements if needed.

## 4. Run
```bat
streamlit run app.py
```

## Free usage note
OpenRouter's free plan currently lists 50 requests per day and 20 requests per minute for free models, while provider-specific limits can also apply. Limits and model availability can change:
- https://openrouter.ai/pricing
- https://openrouter.ai/models?max_price=0
- https://openrouter.ai/docs/api-reference/limits

## Troubleshooting
- **401 / invalid API key:** check `.env` and ensure the key is copied correctly.
- **No endpoints / model unavailable:** choose a different active free model on the OpenRouter models page.
- **429 / rate limit:** wait for the reset or select another eligible free model.
- **FFmpeg not found:** install FFmpeg and add its `bin` folder to PATH.
- **YouTube OAuth error:** verify that YouTube Data API v3 is enabled and `client_secret.json` is in the project folder.
