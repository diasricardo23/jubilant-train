from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import io
from team_balancer import TeamBalancer, Player

app = FastAPI(
    title="Team Balancer API",
    description="API for balancing football teams based on player ratings and positions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class PlayerInput:
    name: str
    overall: float
    position: str

@dataclass
class TeamRequest:
    players: List[PlayerInput]
    num_teams: int = 2
    time_limit: int = 30
    num_attempts: int = 5

@dataclass
class PlayerOutput:
    name: str
    overall: float
    position: str

@dataclass
class TeamOutput:
    team_number: int
    players: List[PlayerOutput]
    average_rating: float
    position_distribution: Dict[str, int]
    total_rating: float

@dataclass
class BalanceResponse:
    teams: List[TeamOutput]
    overall_mean: float
    max_rating_difference: float

@app.post("/balance/json")
async def balance_teams_json(request: TeamRequest):
    """
    Balance teams using JSON input
    """
    try:
        # Create DataFrame from input
        df = pd.DataFrame([{
            'name': p.name,
            'overall': p.overall,
            'position': p.position
        } for p in request.players])
        
        # Save DataFrame to temporary CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Initialize balancer with the CSV data
        balancer = TeamBalancer(csv_buffer)
        
        # Balance teams
        teams = balancer.balance_teams(
            request.num_teams,
            time_limit=request.time_limit,
            num_attempts=request.num_attempts
        )
        
        if not teams:
            raise HTTPException(status_code=400, detail="Could not balance teams with given constraints")
        
        # Calculate overall statistics
        all_players = []
        team_outputs = []
        
        for team_num, players in sorted(teams.items()):
            all_players.extend(players)
            team_rating = sum(p.overall for p in players)
            avg_rating = team_rating / len(players)
            
            # Count positions
            pos_dist = {'DEF': 0, 'MID': 0, 'ATT': 0}
            for p in players:
                pos_dist[p.position] += 1
            
            team_outputs.append(TeamOutput(
                team_number=team_num + 1,
                players=[PlayerOutput(name=p.name, overall=p.overall, position=p.position) 
                        for p in players],
                average_rating=avg_rating,
                position_distribution=pos_dist,
                total_rating=team_rating
            ))
        
        overall_mean = sum(p.overall for p in all_players) / len(all_players)
        team_means = [t.average_rating for t in team_outputs]
        max_diff = max(team_means) - min(team_means)
        
        return BalanceResponse(
            teams=team_outputs,
            overall_mean=overall_mean,
            max_rating_difference=max_diff
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/balance/csv")
async def balance_teams_csv(
    file: UploadFile,
    num_teams: int = 2,
    time_limit: int = 30,
    num_attempts: int = 5
):
    """
    Balance teams using CSV file input
    """
    try:
        # Read CSV content
        content = await file.read()
        csv_buffer = io.StringIO(content.decode())
        
        # Initialize balancer
        balancer = TeamBalancer(csv_buffer)
        
        # Balance teams
        teams = balancer.balance_teams(num_teams, time_limit=time_limit, num_attempts=num_attempts)
        
        if not teams:
            raise HTTPException(status_code=400, detail="Could not balance teams with given constraints")
        
        # Calculate overall statistics
        all_players = []
        team_outputs = []
        
        for team_num, players in sorted(teams.items()):
            all_players.extend(players)
            team_rating = sum(p.overall for p in players)
            avg_rating = team_rating / len(players)
            
            # Count positions
            pos_dist = {'DEF': 0, 'MID': 0, 'ATT': 0}
            for p in players:
                pos_dist[p.position] += 1
            
            team_outputs.append(TeamOutput(
                team_number=team_num + 1,
                players=[PlayerOutput(name=p.name, overall=p.overall, position=p.position) 
                        for p in players],
                average_rating=avg_rating,
                position_distribution=pos_dist,
                total_rating=team_rating
            ))
        
        overall_mean = sum(p.overall for p in all_players) / len(all_players)
        team_means = [t.average_rating for t in team_outputs]
        max_diff = max(team_means) - min(team_means)
        
        return BalanceResponse(
            teams=team_outputs,
            overall_mean=overall_mean,
            max_rating_difference=max_diff
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint returning API information
    """
    return {
        "name": "Team Balancer API",
        "version": "1.0.0",
        "description": "API for balancing football teams based on player ratings and positions",
        "endpoints": {
            "/balance/json": "Balance teams using JSON input",
            "/balance/csv": "Balance teams using CSV file input"
        }
    } 