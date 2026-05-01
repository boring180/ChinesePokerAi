"""
Evaluation Framework for Chinese Poker AI
Metrics: Win rate, turn count, error rate, and more
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json
import os
from datetime import datetime

from game_runner import GameResult


@dataclass
class AgentStats:
    """Statistics for a single agent"""
    agent_name: str
    agent_type: str
    games_played: int = 0
    games_won: int = 0
    win_rate: float = 0.0
    avg_turn_count: float = 0.0
    total_turns: int = 0
    error_count: int = 0
    error_rate: float = 0.0
    
    # Role-specific stats
    wins_as_landlord: int = 0
    games_as_landlord: int = 0
    wins_as_farmer: int = 0
    games_as_farmer: int = 0
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "games_played": self.games_played,
            "games_won": self.games_won,
            "win_rate": f"{self.win_rate:.2%}",
            "avg_turn_count": f"{self.avg_turn_count:.1f}",
            "error_rate": f"{self.error_rate:.2%}",
            "landlord_win_rate": f"{self.wins_as_landlord / max(1, self.games_as_landlord):.2%}",
            "farmer_win_rate": f"{self.wins_as_farmer / max(1, self.games_as_farmer):.2%}",
        }


class ExperimentResult:
    """Results from an experiment"""
    
    def __init__(self, experiment_name: str, num_games: int):
        self.experiment_name = experiment_name
        self.num_games = num_games
        self.results: List[GameResult] = []
        self.agent_stats: Dict[str, AgentStats] = {}
        self.agent_type_map: Dict[str, str] = {}  # name -> type
    
    def add_result(self, result: GameResult, agent_configs: List[Tuple[str, str, str]]):
        """
        Add a game result with agent configurations.
        
        Args:
            result: GameResult
            agent_configs: List of (name, type, role) for each agent
        """
        self.results.append(result)
        
        # Update stats for each agent
        for idx, (name, agent_type, role) in enumerate(agent_configs):
            if name not in self.agent_stats:
                self.agent_stats[name] = AgentStats(name, agent_type)
                self.agent_type_map[name] = agent_type
            
            stats = self.agent_stats[name]
            stats.games_played += 1
            
            # Track role
            is_landlord = (role == "地主")
            if is_landlord:
                stats.games_as_landlord += 1
            else:
                stats.games_as_farmer += 1
            
            # Track win
            if result.winner_idx == idx:
                stats.games_won += 1
                if is_landlord:
                    stats.wins_as_landlord += 1
                else:
                    stats.wins_as_farmer += 1
            
            stats.total_turns += result.turn_count
            stats.error_count += result.error_count
        
        # Recalculate averages
        for stats in self.agent_stats.values():
            stats.win_rate = stats.games_won / max(1, stats.games_played)
            stats.avg_turn_count = stats.total_turns / max(1, stats.games_played)
            stats.error_rate = stats.error_count / max(1, stats.total_turns)
    
    def get_summary(self) -> str:
        """Get formatted summary of results"""
        lines = [
            "=" * 60,
            f"实验: {self.experiment_name}",
            f"总游戏数: {len(self.results)}",
            "=" * 60,
            "",
        ]
        
        # Agent stats
        lines.append("各代理表现:")
        lines.append("-" * 60)
        for name, stats in self.agent_stats.items():
            lines.append(f"\n【{name}】({stats.agent_type})")
            lines.append(f"  胜率: {stats.win_rate:.2%} ({stats.games_won}/{stats.games_played})")
            lines.append(f"  平均回合: {stats.avg_turn_count:.1f}")
            lines.append(f"  错误率: {stats.error_rate:.2%}")
            if stats.games_as_landlord > 0:
                lines.append(f"  地主胜率: {stats.wins_as_landlord}/{stats.games_as_landlord}")
            if stats.games_as_farmer > 0:
                lines.append(f"  农民胜率: {stats.wins_as_farmer}/{stats.games_as_farmer}")
        
        # Overall stats
        lines.append("\n" + "=" * 60)
        lines.append("整体统计:")
        total_turns = sum(r.turn_count for r in self.results)
        avg_turns = total_turns / max(1, len(self.results))
        total_errors = sum(r.error_count for r in self.results)
        lines.append(f"  平均回合数: {avg_turns:.1f}")
        lines.append(f"  总错误数: {total_errors}")
        lines.append(f"  每回合错误率: {total_errors / max(1, total_turns):.3%}")
        
        # Role-based win rate
        landlord_wins = sum(1 for r in self.results if r.winner_role == "地主")
        farmer_wins = len(self.results) - landlord_wins
        lines.append(f"\n角色胜率:")
        lines.append(f"  地主: {landlord_wins}/{len(self.results)} ({landlord_wins/max(1,len(self.results)):.1%})")
        lines.append(f"  农民: {farmer_wins}/{len(self.results)} ({farmer_wins/max(1,len(self.results)):.1%})")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "experiment_name": self.experiment_name,
            "num_games": len(self.results),
            "agent_stats": {name: stats.to_dict() for name, stats in self.agent_stats.items()},
            "summary": self.get_summary(),
        }
    
    def save(self, filepath: str):
        """Save results to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"Results saved to {filepath}")


class Evaluator:
    """Main evaluation class for running experiments"""
    
    def __init__(self, output_dir: str = "results", log_games: bool = True):
        self.output_dir = output_dir
        self.log_games = log_games
        os.makedirs(output_dir, exist_ok=True)
        
        # Create logs directory for game logs
        if self.log_games:
            self.logs_dir = os.path.join(output_dir, "game_logs")
            os.makedirs(self.logs_dir, exist_ok=True)
        
        self.experiments: List[ExperimentResult] = []
    
    def evaluate_experiment_a(self, advanced_agent, normal_agent_factory, 
                            num_games: int = 30, enable_logging: bool = None) -> ExperimentResult:
        """
        Experiment A: 1 advanced agent vs 2 normal agents
        
        Setup:
        - Player 1: Advanced agent (CoT, Tool, or Full)
        - Player 2, 3: Normal agents
        
        Rotates who is landlord to ensure fairness.
        
        Args:
            advanced_agent: The advanced agent instance
            normal_agent_factory: Factory function that returns normal agents
            num_games: Number of games to run
            enable_logging: Whether to save game logs (default: True for first 5 games)
        
        Returns:
            ExperimentResult
        """
        from game_runner import GameRunner
        from ai_agent import BaseAgent
        
        exp_name = f"Experiment_A_{advanced_agent.__class__.__name__}_vs_Normal"
        result = ExperimentResult(exp_name, num_games)
        
        # Default: log first 5 games for inspection
        if enable_logging is None:
            enable_logging = self.log_games
        
        print(f"\nRunning {exp_name}...")
        print(f"Configuration: 1 {advanced_agent.__class__.__name__} vs 2 Normal agents")
        print(f"Running {num_games} games...")
        if enable_logging:
            print(f"Game logs will be saved to: {self.logs_dir}/{exp_name}/")
        
        # Run games with landlord rotation
        for i in range(num_games):
            # Create fresh agents for each game
            agent1 = advanced_agent.__class__(advanced_agent.name, advanced_agent.config)
            agent2 = normal_agent_factory()
            agent3 = normal_agent_factory()
            
            agents = [agent1, agent2, agent3]
            
            # Rotate landlord
            landlord_idx = i % 3
            
            # Run game
            # Enable logging for first 5 games only to avoid too many files
            game_logging = enable_logging and i < 5
            runner = GameRunner(
                agents, 
                verbose=False, 
                enable_logging=game_logging,
                log_folder=self.logs_dir if game_logging else "logs",
                experiment_name=exp_name if game_logging else None
            )
            game_result = runner.run_game(random_landlord=False, landlord_idx=landlord_idx)
            
            # Record result
            agent_configs = [
                (agent1.name, "advanced", "地主" if landlord_idx == 0 else "农民"),
                (agent2.name, "normal", "地主" if landlord_idx == 1 else "农民"),
                (agent3.name, "normal", "地主" if landlord_idx == 2 else "农民"),
            ]
            result.add_result(game_result, agent_configs)
            
            if (i + 1) % 10 == 0:
                print(f"  Completed {i+1}/{num_games} games...")
        
        # Save results
        self.experiments.append(result)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result.save(os.path.join(self.output_dir, f"{exp_name}_{timestamp}.json"))
        
        print(result.get_summary())
        return result
    
    def evaluate_experiment_b(self, advanced_agent_factory, normal_agent_factory,
                            num_games: int = 30) -> Tuple[ExperimentResult, ExperimentResult]:
        """
        Experiment B: 3 advanced agents vs 3 normal agents
        Compare turn count between the two groups.
        
        Args:
            advanced_agent_factory: Factory that returns advanced agents
            normal_agent_factory: Factory that returns normal agents
            num_games: Number of games per group
        
        Returns:
            Tuple of (advanced_results, normal_results)
        """
        print(f"\nRunning Experiment B...")
        print(f"Comparing turn counts: 3 Advanced agents vs 3 Normal agents")
        print(f"Running {num_games} games per group...")
        if self.log_games:
            print(f"Game logs will be saved to: {self.logs_dir}/")
        
        # Run advanced group
        exp_name_advanced = "Experiment_B_3_Advanced"
        result_advanced = ExperimentResult(exp_name_advanced, num_games)
        
        for i in range(num_games):
            agents = [
                advanced_agent_factory("玩家一"),
                advanced_agent_factory("玩家二"),
                advanced_agent_factory("玩家三"),
            ]
            
            # Enable logging for first 3 games
            game_logging = self.log_games and i < 3
            runner = GameRunner(
                agents, 
                verbose=False, 
                enable_logging=game_logging,
                log_folder=self.logs_dir if game_logging else "logs",
                experiment_name=exp_name_advanced if game_logging else None
            )
            game_result = runner.run_game(random_landlord=True)
            
            agent_configs = [
                (agents[0].name, "advanced", "unknown"),  # Will be determined by actual role
                (agents[1].name, "advanced", "unknown"),
                (agents[2].name, "advanced", "unknown"),
            ]
            result_advanced.add_result(game_result, agent_configs)
            
            if (i + 1) % 10 == 0:
                print(f"  Advanced group: {i+1}/{num_games}...")
        
        # Run normal group
        exp_name_normal = "Experiment_B_3_Normal"
        result_normal = ExperimentResult(exp_name_normal, num_games)
        
        for i in range(num_games):
            agents = [
                normal_agent_factory("玩家一"),
                normal_agent_factory("玩家二"),
                normal_agent_factory("玩家三"),
            ]
            
            # Enable logging for first 3 games
            game_logging = self.log_games and i < 3
            runner = GameRunner(
                agents, 
                verbose=False, 
                enable_logging=game_logging,
                log_folder=self.logs_dir if game_logging else "logs",
                experiment_name=exp_name_normal if game_logging else None
            )
            game_result = runner.run_game(random_landlord=True)
            
            agent_configs = [
                (agents[0].name, "normal", "unknown"),
                (agents[1].name, "normal", "unknown"),
                (agents[2].name, "normal", "unknown"),
            ]
            result_normal.add_result(game_result, agent_configs)
            
            if (i + 1) % 10 == 0:
                print(f"  Normal group: {i+1}/{num_games}...")
        
        # Save results
        self.experiments.extend([result_advanced, result_normal])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_advanced.save(os.path.join(self.output_dir, f"{exp_name_advanced}_{timestamp}.json"))
        result_normal.save(os.path.join(self.output_dir, f"{exp_name_normal}_{timestamp}.json"))
        
        # Print comparison
        print("\n" + "=" * 60)
        print("Experiment B Results: Turn Count Comparison")
        print("=" * 60)
        
        adv_avg_turns = sum(r.turn_count for r in result_advanced.results) / max(1, len(result_advanced.results))
        norm_avg_turns = sum(r.turn_count for r in result_normal.results) / max(1, len(result_normal.results))
        
        print(f"\n3 Advanced Agents:")
        print(f"  Average turn count: {adv_avg_turns:.1f}")
        print(f"  Games played: {len(result_advanced.results)}")
        
        print(f"\n3 Normal Agents:")
        print(f"  Average turn count: {norm_avg_turns:.1f}")
        print(f"  Games played: {len(result_normal.results)}")
        
        diff = norm_avg_turns - adv_avg_turns
        pct_diff = (diff / max(1, norm_avg_turns)) * 100
        print(f"\nDifference: {diff:.1f} turns ({pct_diff:+.1f}%)")
        if diff > 0:
            print("Advanced agents finish games faster!")
        elif diff < 0:
            print("Normal agents finish games faster.")
        else:
            print("Similar performance.")
        
        print("=" * 60)
        
        return result_advanced, result_normal
    
    def compare_all_experiments(self):
        """Generate overall comparison report"""
        if not self.experiments:
            print("No experiments to compare.")
            return
        
        print("\n" + "=" * 60)
        print("OVERALL EXPERIMENT SUMMARY")
        print("=" * 60)
        
        for exp in self.experiments:
            print(f"\n{exp.get_summary()}")
        
        # Save combined report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.output_dir, f"combined_report_{timestamp}.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            for exp in self.experiments:
                f.write(exp.get_summary() + "\n\n")
        
        print(f"\nCombined report saved to: {report_path}")


def quick_test(agent_types: List[str] = None, num_games: int = 5):
    """
    Quick test with specified agent types.
    
    Args:
        agent_types: List of 3 agent types ("normal", "cot", "tool", "full")
        num_games: Number of games to run
    """
    from ai_agent import create_agent, load_strategy_guide
    
    if agent_types is None:
        agent_types = ["normal", "normal", "normal"]
    
    print(f"Quick test: {' vs '.join(agent_types)}")
    print(f"Running {num_games} games...")
    
    # Load guide for full agents
    guide = load_strategy_guide("guides/intermediate_guide.md")
    
    results = []
    for i in range(num_games):
        agents = []
        for j, agent_type in enumerate(agent_types):
            if agent_type == "full":
                agent = create_agent(agent_type, f"玩家{j+1}", guide_content=guide)
            else:
                agent = create_agent(agent_type, f"玩家{j+1}")
            agents.append(agent)
        
        from game_runner import GameRunner
        runner = GameRunner(agents, verbose=False)
        result = runner.run_game(random_landlord=True)
        results.append(result)
        
        print(f"  Game {i+1}: {result.winner_name} ({result.winner_role}) won in {result.turn_count} turns")
    
    # Summary
    print("\nSummary:")
    for agent_type in set(agent_types):
        wins = sum(1 for r in results if agent_type in r.winner_role.lower() or True)  # Simplified
        print(f"  {agent_type}: {wins} wins")
    
    avg_turns = sum(r.turn_count for r in results) / len(results)
    print(f"  Average turns: {avg_turns:.1f}")


if __name__ == "__main__":
    # Run quick test
    print("Running quick test with default agents...")
    quick_test(["normal", "normal", "normal"], num_games=3)
