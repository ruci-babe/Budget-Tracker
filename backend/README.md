# Expense Tracker - Sync Backend API

This is the backend server that enables syncing transactions between desktop and mobile applications.

## Features

- 🔐 User authentication with JWT tokens
- 📱 Device registration and management
- 💰 Transaction sync across multiple devices
- 📊 Category management per user
- 📋 Sync logging for conflict resolution
- 🔄 Bidirectional sync support

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, SQLite works too)

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Initialize database
python -c "from app import init_db; init_db()"

# Run server
python app.py
```

### Using Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

### Devices
- `POST /devices/register` - Register a device for sync

### Transactions
- `GET /transactions` - Get user's transactions
- `POST /transactions/sync` - Sync transactions from device

## API Examples

### Register User
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'
```

### Register Device
```bash
curl -X POST http://localhost:5000/devices/register \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "My Android Phone",
    "device_type": "android",
    "device_id": "unique-device-uuid"
  }'
```

### Sync Transactions
```bash
curl -X POST http://localhost:5000/transactions/sync \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "unique-device-uuid",
    "transactions": [
      {
        "date": "2026-04-10",
        "description": "Coffee",
        "amount": 5.50,
        "vendor": "Starbucks",
        "payment_method": "card"
      }
    ],
    "last_sync": "2026-04-10T12:00:00"
  }'
```

## Database Schema

### Users
- id, username, email, password_hash, created_at, last_sync

### Devices
- id, user_id, device_name, device_type, device_id, last_seen, created_at

### Transactions
- id, user_id, category_id, date, description, amount, vendor, payment_method, is_recurring, is_duplicate, receipt_image, notes, created_at, updated_at, synced_at, device_id

### Categories
- id, user_id, name, color, icon, created_at, updated_at

### SyncLogs
- id, device_id, sync_type, items_synced, conflicts, status, error_message, synced_at

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t expense-tracker-api .
docker run -e DATABASE_URL=postgresql://user:pass@db:5432/tracker -p 5000:5000 expense-tracker-api
```

### Using with Android App
The Android mobile app will use this backend for:
1. User registration/login
2. Syncing new expenses from mobile to desktop
3. Pulling updated categories and transactions from desktop
4. Conflict resolution for simultaneous edits

## Security Considerations

⚠️ **Before deploying to production:**
1. Change `SECRET_KEY` in `.env` to a strong random value
2. Use HTTPS/SSL in production
3. Use PostgreSQL instead of SQLite for production
4. Set up proper firewall rules
5. Enable CORS only for authorized origins
6. Use environment variables for all sensitive data
7. Implement rate limiting
8. Set up monitoring and logging

## Development

### Run tests
```bash
# Coming soon - test suite for sync API
```

### Database migrations
```bash
# Currently using SQLAlchemy auto-schema creation
# For production, consider using Alembic for migrations
```
