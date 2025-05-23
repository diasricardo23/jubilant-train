import pandas as pd
from pulp import *
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
import sys
import random
import time

@dataclass
class Player:
    name: str
    overall: float  # Rating from 0 to 5
    position: str  # DEF, MID, or ATT

class TeamBalancer:
    def __init__(self, csv_path_or_buffer):
        self.players = self._load_players(csv_path_or_buffer)
        # Count players by position
        pos_counts = defaultdict(int)
        for player in self.players:
            pos_counts[player.position] += 1
            
        # Minimum requirements (at least 2 of each position)
        self.position_requirements = {
            'DEF': 2,
            'MID': 2,
            'ATT': 2
        }
            
        print(f"Players per position: {dict(pos_counts)}")
        print(f"Total players: {len(self.players)}")
        print(f"Minimum position requirements per team: {self.position_requirements}")

    def _load_players(self, csv_path_or_buffer) -> List[Player]:
        """Load players from CSV file or buffer."""
        df = pd.read_csv(csv_path_or_buffer)
        players = []
        
        for _, row in df.iterrows():
            player = Player(
                name=row['name'],
                overall=float(row['overall']),
                position=str(row['position']).strip()  # Clean up position string
            )
            players.append(player)
        
        # Shuffle the players list to add randomness
        random.shuffle(players)
        return players

    def _try_balance_teams(self, num_teams: int, time_limit: int = 30, rating_threshold: float = 0.1) -> Tuple[Dict[int, List[Player]], float]:
        """
        Try to balance teams with some randomness while keeping them balanced.
        Returns a tuple of (teams dict, max rating difference)
        """
        # Create the optimization problem
        prob = LpProblem("Team_Balancing", LpMinimize)

        # Create binary variables for each player-team combination
        player_vars = LpVariable.dicts("player",
                                     ((i, j) for i in range(len(self.players)) 
                                      for j in range(num_teams)),
                                     cat='Binary')

        # Each player must be assigned to exactly one team
        for i in range(len(self.players)):
            prob += lpSum(player_vars[i,j] for j in range(num_teams)) == 1

        # Calculate average team rating
        total_rating = sum(p.overall for p in self.players)
        target_team_rating = total_rating / num_teams

        # Create variables for team rating differences
        max_diff = LpVariable("max_diff", 0)
        
        # Calculate team ratings and set up the objective to minimize maximum difference
        for j in range(num_teams):
            team_rating = lpSum(self.players[i].overall * player_vars[i,j] 
                              for i in range(len(self.players)))
            
            # Allow some randomness within the threshold
            prob += max_diff >= (team_rating - target_team_rating) - random.uniform(0, rating_threshold)
            prob += max_diff >= (target_team_rating - team_rating) - random.uniform(0, rating_threshold)

        # Set the objective to minimize the maximum difference
        prob += max_diff

        # Position requirements for each team (minimum requirements)
        for j in range(num_teams):
            for pos, min_count in self.position_requirements.items():
                prob += lpSum(player_vars[i,j] 
                            for i in range(len(self.players)) 
                            if self.players[i].position == pos) >= min_count

            # Each team should have the same total number of players
            prob += lpSum(player_vars[i,j] 
                        for i in range(len(self.players))) == len(self.players) // num_teams

        # Solve the problem with time limit
        solver = PULP_CBC_CMD(timeLimit=time_limit, msg=False)  # Disable solver output
        status = prob.solve(solver)

        # Extract the results
        teams = defaultdict(list)
        max_rating_diff = float('inf')
        
        if LpStatus[prob.status] == 'Optimal' or LpStatus[prob.status] == 'Not Solved':
            for i in range(len(self.players)):
                for j in range(num_teams):
                    if value(player_vars[i,j]) == 1:
                        teams[j].append(self.players[i])
            
            if teams:
                # Calculate actual maximum rating difference
                team_ratings = [sum(p.overall for p in players) / len(players) 
                              for players in teams.values()]
                max_rating_diff = max(team_ratings) - min(team_ratings)
                
        return dict(teams), max_rating_diff

    def balance_teams(self, num_teams: int, time_limit: int = 30, num_attempts: int = 5) -> Dict[int, List[Player]]:
        """
        Try multiple times to get balanced teams with some randomness.
        Args:
            num_teams: Number of teams to create
            time_limit: Maximum time in seconds for each attempt
            num_attempts: Number of attempts to try different random combinations
        Returns:
            Dictionary with team number as key and list of players as value.
        """
        # Validate that teams can be divided equally
        total_players = len(self.players)
        if total_players % num_teams != 0:
            print(f"\nError: Cannot divide {total_players} players into {num_teams} equal teams.")
            print(f"The number of players must be divisible by the number of teams.")
            print(f"Current players: {total_players}")
            print(f"Players needed per team: {total_players / num_teams}")
            return {}

        players_per_team = total_players // num_teams
        print(f"\nCreating {num_teams} teams with {players_per_team} players each")
        
        # Try multiple times with different random seeds
        best_teams = {}
        best_diff = float('inf')
        
        for attempt in range(num_attempts):
            print(f"\nAttempt {attempt + 1}/{num_attempts}...")
            # Shuffle players for each attempt
            random.shuffle(self.players)
            
            # Try to balance teams
            teams, max_diff = self._try_balance_teams(num_teams, time_limit // num_attempts)
            
            # Keep the best result
            if teams and max_diff < best_diff:
                best_teams = teams
                best_diff = max_diff
        
        if best_teams:
            print(f"\nFound solution with maximum rating difference: {best_diff:.2f}")
            print(f"Solution status: Optimal")
        else:
            print("Could not find a solution. Try adjusting the requirements or increasing the time limit.")

        return best_teams

    def print_teams(self, teams: Dict[int, List[Player]]):
        """Print the balanced teams with their statistics."""
        if not teams:
            return
            
        print("\n=== BALANCED TEAMS ===\n")
        
        team_means = []  # Store team means for final comparison
        all_players = []  # Store all players for overall mean
        
        # Sort teams by team number
        sorted_teams = sorted(teams.items(), key=lambda x: x[0])
        
        for team_num, players in sorted_teams:
            print(f"\nTeam {team_num + 1}:")
            print("-" * 50)
            team_overall = sum(p.overall for p in players) / len(players)
            team_means.append(team_overall)
            all_players.extend(players)
            
            print(f"Average Rating: {team_overall:.2f}")
            print("\nPlayers by Position:")
            
            # Group and sort players by position
            players_by_pos = defaultdict(list)
            for player in players:
                players_by_pos[player.position].append(player)
            
            for pos in ['DEF', 'MID', 'ATT']:
                print(f"\n{pos}:")
                # Sort players in position by rating
                pos_players = sorted(players_by_pos[pos], key=lambda p: -p.overall)
                for player in pos_players:
                    print(f"- {player.name} (Rating: {player.overall:.1f})")
            
            print(f"\nPosition Distribution:")
            pos_count = defaultdict(int)
            for player in players:
                pos_count[player.position] += 1
            for pos in ['DEF', 'MID', 'ATT']:
                print(f"{pos}: {pos_count[pos]}")
            
            print(f"\nTotal Team Rating: {sum(p.overall for p in players):.2f}")
            print("-" * 50)
        
        # Print overall statistics
        print("\n=== OVERALL STATISTICS ===")
        print("-" * 50)
        overall_mean = sum(p.overall for p in all_players) / len(all_players)
        print(f"Overall player mean rating: {overall_mean:.2f}")
        
        print("\nTeam Means:")
        for i, mean in enumerate(team_means):
            print(f"Team {i + 1}: {mean:.2f}")
            
        max_diff = max(team_means) - min(team_means)
        print(f"\nMaximum difference between team means: {max_diff:.2f}")
        print("-" * 50)

def main():
    # Set random seed based on current time
    random.seed(time.time())
    
    # Initialize the balancer with the CSV file
    balancer = TeamBalancer('sample_players.csv')
    
    # Get number of teams from command line argument or default to 2
    num_teams = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    
    # Balance teams with multiple attempts
    balanced_teams = balancer.balance_teams(num_teams, time_limit=30, num_attempts=5)
    
    # Print the results
    balancer.print_teams(balanced_teams)

if __name__ == "__main__":
    main() 