# Environment Variables Setup

This project now uses `python-decouple` to manage environment variables.

## Installation

The required package has been added to `requirements.txt`. To install it, run:

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root (same directory as `manage.py`):
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual values:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   LIGHTNING_API_KEY=your-lightning-api-key-here
   ```

## Available Environment Variables

The following environment variables are now supported in `sds/settings.py`:

- **SECRET_KEY**: Django secret key (defaults to development key if not set)
- **DEBUG**: Debug mode (defaults to True if not set, accepts True/False)
- **LIGHTNING_API_KEY**: Lightning API key (defaults to empty string if not set)

## How It Works

The `config()` function from `python-decouple` reads values from:
1. Environment variables first
2. `.env` file if environment variable is not set
3. Default value if neither is available

Example usage in `settings.py`:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='fallback-value')
DEBUG = config('DEBUG', default=True, cast=bool)
LIGHTNING_API_KEY = config('LIGHTNING_API_KEY', default='')
```

## Security Notes

- The `.env` file is already in `.gitignore` and should NEVER be committed
- Always use strong, unique values for `SECRET_KEY` in production
- Set `DEBUG=False` in production environments
- Store sensitive credentials only in `.env` file or environment variables
