# Team Balancer API (Backend)

The backend service for the Team Balancer application, built with FastAPI.

## Features

- Balance teams based on player ratings and positions
- Support for both JSON and CSV input
- Configurable number of teams
- Optimization for balanced team composition

## API Endpoints

- `GET /` - API information
- `POST /balance/json` - Balance teams using JSON input
- `POST /balance/csv` - Balance teams using CSV file upload

## Local Development

1. Navigate to the backend directory:
```bash
cd balancer_backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
uvicorn api:app --reload
```

The API will be available at http://localhost:8000

## Deployment

### Deploy to Render

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Render will automatically detect the Python environment and deploy

The `render.yaml` file is already configured for deployment.

## API Documentation

Once deployed, visit:
- `/docs` for Swagger UI documentation
- `/redoc` for ReDoc documentation

## Example JSON Request

```json
{
    "players": [
        {
            "name": "Player 1",
            "overall": 4.5,
            "position": "ATT"
        }
    ],
    "num_teams": 2,
    "time_limit": 30,
    "num_attempts": 5
}
```

## Example CSV Format

```csv
name,overall,position
Player 1,4.5,ATT
Player 2,3.8,DEF
Player 3,2.7,MID
```

## Project Structure

```
balancer_backend/
├── api.py              # FastAPI application
├── team_balancer.py    # Team balancing logic
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment configuration
├── sample_players.csv  # Example CSV data
└── sample_players.json # Example JSON data
``` 