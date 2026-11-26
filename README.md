# Google Map Searcher LINE Bot

Flask-based LINE Bot that extracts places from Instagram, Threads, and Facebook content using Gemini and replies with Google Maps search links.

## Configuration

The application calls `load_dotenv()` at startup, so local development reads a `.env` file in the project directory. Existing process environment variables take precedence over `.env` values (the default `python-dotenv` behavior).

Create your local configuration from the example; never commit `.env` or place real secrets in `.env.example`.

```bash
cp .env.example .env
```

Required secrets:

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `GEMINI_API_KEY`
- `RAPIDAPI_KEY`

Listener settings:

- `APP_HOST` defaults to `127.0.0.1`.
- `APP_PORT` defaults to `5000`.

For the production Nginx reverse-proxy layout, retain `APP_HOST=127.0.0.1` and `APP_PORT=5000`. Do not expose port 5000 publicly.

## Local startup

Use Python 3 and install the dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The default listener is `http://127.0.0.1:5000`. To override it for an isolated local test:

```bash
APP_HOST=127.0.0.1 APP_PORT=5050 python app.py
```

On Windows PowerShell:

```powershell
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '5050'
python app.py
```

## Oracle Cloud deployment layout

Production location: `/home/ubuntu/google-map-searcher` on Ubuntu 22.04. The `linebot.service` systemd service runs the app, and Nginx configuration at `/etc/nginx/sites-available/linebot` proxies `/callback` to `http://127.0.0.1:5000`.

1. Update application files and dependencies in `/home/ubuntu/google-map-searcher`.
2. Keep production secrets in the existing private `.env` (or set them in `linebot.service` using `EnvironmentFile=`); do not commit it.
3. Ensure the service supplies or inherits `APP_HOST=127.0.0.1` and `APP_PORT=5000`. These values must match Nginx's upstream.
4. Verify the Nginx upstream remains `proxy_pass http://127.0.0.1:5000;` for `/callback`.
5. After a planned release, validate configuration and restart in the normal operational window:

   ```bash
   sudo nginx -t
   sudo systemctl restart linebot.service
   sudo systemctl status linebot.service
   sudo journalctl -u linebot.service -n 100 --no-pager
   ```

## Production note

`app.run()` is Flask's development server and is not intended for robust public production serving. Its localhost binding and Nginx proxy reduce direct exposure, but it lacks a production WSGI server's concurrency, lifecycle, and resilience characteristics. A future hardening change should run the Flask app behind Gunicorn (or uWSGI) under systemd, leaving Nginx as the TLS/reverse-proxy endpoint. This change deliberately does not alter the current web server or service architecture.
