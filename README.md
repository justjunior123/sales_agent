# HappyRobot Inbound Carrier Sales Agent

A proof-of-concept inbound carrier sales agent built for the HappyRobot FDE Technical Challenge. This system handles carrier calls, authenticates them via FMCSA, matches viable loads, negotiates pricing, and provides real-time analytics through a dashboard.

## Overview

When a carrier calls in requesting loads, this system:
1. **Verifies** their credentials via FMCSA API
2. **Searches** for matching loads based on their requirements
3. **Negotiates** pricing within defined guardrails
4. **Extracts** key call data using rule-based patterns
5. **Classifies** call outcomes and sentiment
6. **Logs** everything for analytics and reporting

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite
- **Dashboard**: Streamlit
- **Deployment**: Docker + Render
- **APIs**: FMCSA Carrier Verification

## Project Structure

```
sales_agent/
├── app/
│   ├── api/
│   │   ├── models.py           # Pydantic request/response models
│   │   └── routes.py           # API endpoints
│   ├── services/
│   │   ├── verification.py     # FMCSA carrier verification
│   │   ├── search.py           # Load matching logic
│   │   ├── negotiation.py      # Pricing guardrails
│   │   ├── extraction.py       # Call data extraction
│   │   └── classification.py   # Outcome & sentiment classification
│   ├── data/
│   │   ├── loads.json          # Sample load database
│   │   └── db.py               # SQLite operations
│   └── main.py                 # FastAPI application
├── streamlit/
│   └── dashboard.py            # Analytics dashboard
├── deployment/
│   ├── render.yaml             # Render deployment config
│   └── DEPLOYMENT.md           # Deployment guide
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd sales_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your FMCSA_API_KEY
```

### 3. Run Locally

**Option A: Direct Python**

```bash
# Start API
python -m uvicorn app.main:app --reload --port 8000

# In another terminal, start dashboard
streamlit run streamlit/dashboard.py
```

**Option B: Docker Compose**

```bash
docker-compose up --build
```

Access:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/verify_carrier` | POST | Verify carrier via MC number |
| `/api/v1/search_loads` | POST | Search for matching loads |
| `/api/v1/evaluate_offer` | POST | Evaluate counter-offers |
| `/api/v1/extract_call_data` | POST | Extract structured data from transcript |
| `/api/v1/classify_call` | POST | Classify outcome & sentiment |
| `/api/v1/call_logs` | GET | Retrieve call logs with filters |

### Example Usage

**Verify Carrier**
```bash
curl -X POST http://localhost:8000/api/v1/verify_carrier \
  -H "Content-Type: application/json" \
  -d '{"mc_number": "MC123456"}'
```

**Search Loads**
```bash
curl -X POST http://localhost:8000/api/v1/search_loads \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Los Angeles, CA",
    "destination": "Houston, TX",
    "equipment_type": "53ft Dry Van"
  }'
```

**Evaluate Offer**
```bash
curl -X POST http://localhost:8000/api/v1/evaluate_offer \
  -H "Content-Type: application/json" \
  -d '{
    "original_rate": 2500,
    "counter_rate": 2300,
    "load_id": "LD001"
  }'
```

## Features

### 1. FMCSA Integration
- Real API integration with retry logic
- Exponential backoff for rate limits
- Graceful error handling
- Mock mode for testing

### 2. Intelligent Load Matching
- Multi-factor scoring algorithm
- Location matching (city, state, partial)
- Equipment type matching
- Date proximity scoring
- Weighted match confidence

### 3. Negotiation Guardrails
- Floor: loadboard_rate - 10%
- Ceiling: loadboard_rate + 5%
- Max 3 negotiation rounds
- Intelligent counter-offer generation

### 4. Rule-Based Extraction
- Load ID patterns (LD001, Load 001, etc.)
- Currency extraction ($2500, 2,500 dollars)
- MC number detection
- Negotiation round counting
- Call duration estimation

### 5. Call Classification
- Outcome: booked, negotiated, rejected
- Sentiment: positive, neutral, negative
- Confidence scoring
- Keyword-based analysis

### 6. Analytics Dashboard
- Real-time call metrics
- Outcome distribution (pie charts)
- Sentiment analysis
- Pricing trends (board rate vs agreed rate)
- Recent call logs with filtering
- CSV export

### 7. Demo Mode (NEW!)
- **One-click data loading**: Load 8 sample calls instantly
- **One-click data clearing**: Reset to empty state
- **Perfect for demos**: No scripts to run, no CLI commands
- **Video-ready**: Quick iterations for recording walkthroughs
- Built-in dashboard controls with visual feedback

**How to use:**
1. Open dashboard sidebar
2. Find "🎬 Demo Controls"
3. Click "📊 Load" to populate data
4. Click "🗑️ Clear" to reset
5. Refresh browser to see changes

## Deployment

### Deploy to Render

See detailed instructions in [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)

**Quick Deploy:**
1. Push code to GitHub
2. Connect repository to Render
3. Add FMCSA_API_KEY environment variable
4. Deploy!

Your API will be live at: `https://your-app-name.onrender.com`

## HappyRobot Agent Configuration

The HappyRobot agent follows this workflow:

1. **Greeting** → Agent answers call
2. **Verification** → POST `/verify_carrier` with MC number
3. **Load Search** → POST `/search_loads` with requirements
4. **Load Pitch** → Agent presents top match
5. **Negotiation Loop** → POST `/evaluate_offer` for counter-offers (max 3 rounds)
6. **Call Extraction** → POST `/extract_call_data` with transcript
7. **Classification** → POST `/classify_call` for outcome/sentiment
8. **Logging** → POST `/log_call` to save record

## Testing

```bash
# Install dev dependencies
pip install pytest httpx

# Run tests
pytest tests/
```

## Development

### Adding New Loads

Edit `app/data/loads.json` and add load objects:

```json
{
  "load_id": "LD011",
  "origin": "City, State",
  "destination": "City, State",
  "pickup_datetime": "2025-11-20T08:00:00",
  "delivery_datetime": "2025-11-24T18:00:00",
  "equipment_type": "53ft Dry Van",
  "loadboard_rate": 2500,
  "weight": 40000,
  "commodity_type": "General Freight",
  "notes": "Special instructions",
  "miles": 1500
}
```

### Adjusting Negotiation Guardrails

Edit `app/services/negotiation.py`:

```python
FLOOR_PERCENTAGE = 0.10  # 10% below board rate
CEILING_PERCENTAGE = 0.05  # 5% above board rate
```

## Architecture Decisions

### Why This Approach?

- **FastAPI**: Fast, modern, production-ready Python framework
- **Streamlit**: Simple, effective dashboard without overengineering
- **SQLite**: Perfect for POC, easy to migrate to PostgreSQL
- **Rule-Based NLP**: Transparent, debuggable, no LLM API costs
- **Render**: Free tier, familiar platform, no deployment friction

### What's NOT Included (Intentionally)

- Over-engineered ML models
- Complex state machines
- Heavy frontend frameworks
- Authentication/authorization (POC scope)
- Production-grade database (SQLite is ephemeral on Render free tier)

## License

MIT

## Contact

For questions about this implementation, see CLAUDE.md for detailed decision log.
