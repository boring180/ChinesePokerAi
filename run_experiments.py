"""
Main Experiment Runner for Chinese Poker AI Research
Run all experiments or specific ones with configurable parameters.
"""

import sys
import os
import argparse
from datetime import datetime

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiments.experiment_a import run_experiment_a
from experiments.experiment_b import run_experiment_b
from evaluation import Evaluator


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def run_single_game_test():
    """Run a single test game to verify setup"""
    print_header("QUICK TEST: Single Game Verification")
    
    from game_runner import GameRunner
    from ai_agent import NormalAgent, AgentConfig
    
    agents = [
        NormalAgent("玩家一", AgentConfig()),
        NormalAgent("玩家二", AgentConfig()),
        NormalAgent("玩家三", AgentConfig()),
    ]
    
    print("Running single test game with 3 Normal agents...")
    runner = GameRunner(agents, verbose=True)
    result = runner.run_game(random_landlord=True)
    
    print(f"\n✓ Test complete!")
    print(f"  Winner: {result.winner_name} ({result.winner_role})")
    print(f"  Turns: {result.turn_count}")
    print(f"  Errors: {result.error_count}")


def run_experiment_a_all(num_games: int = 30):
    """Run Experiment A with all agent types"""
    print_header("EXPERIMENT A: Win Rate Comparison (1 Advanced vs 2 Normal)")
    
    results = {}
    for agent_type in ["cot", "tool", "full"]:
        print(f"\n{'='*70}")
        print(f" Testing {agent_type.upper()} Agent")
        print(f"{'='*70}")
        result = run_experiment_a(agent_type, num_games)
        results[agent_type] = result
    
    # Summary
    print_header("EXPERIMENT A SUMMARY")
    print(f"\n{'Agent Type':<12} {'Win Rate':<12} {'Avg Turns':<12} {'As Landlord':<15} {'As Farmer'}")
    print("-" * 70)
    
    for agent_type, result in results.items():
        stats = result.agent_stats.get('高级玩家')
        if stats:
            landlord_wr = stats.wins_as_landlord / max(1, stats.games_as_landlord)
            farmer_wr = stats.wins_as_farmer / max(1, stats.games_as_farmer)
            print(f"{agent_type.upper():<12} {stats.win_rate:<12.1%} {stats.avg_turn_count:<12.1f} "
                  f"{landlord_wr:<15.1%} {farmer_wr:.1%}")
    
    return results


def run_experiment_b_all(num_games: int = 30):
    """Run Experiment B with all agent types"""
    print_header("EXPERIMENT B: Turn Count Comparison (3 Advanced vs 3 Normal)")
    
    results = {}
    for agent_type in ["cot", "tool", "full"]:
        print(f"\n{'='*70}")
        print(f" Testing {agent_type.upper()} Agents")
        print(f"{'='*70}")
        adv_result, norm_result = run_experiment_b(agent_type, num_games)
        results[agent_type] = (adv_result, norm_result)
    
    # Summary
    print_header("EXPERIMENT B SUMMARY")
    print(f"\n{'Agent Type':<12} {'Adv Turns':<12} {'Norm Turns':<12} {'Improvement':<15} {'Effect Size'}")
    print("-" * 70)
    
    import statistics
    for agent_type, (adv, norm) in results.items():
        adv_turns = [r.turn_count for r in adv.results]
        norm_turns = [r.turn_count for r in norm.results]
        
        adv_avg = statistics.mean(adv_turns)
        norm_avg = statistics.mean(norm_turns)
        improvement = ((norm_avg - adv_avg) / norm_avg) * 100
        
        # Effect size
        pooled_std = ((statistics.stdev(adv_turns)**2 + statistics.stdev(norm_turns)**2) / 2) ** 0.5
        cohens_d = (norm_avg - adv_avg) / pooled_std if pooled_std > 0 else 0
        
        print(f"{agent_type.upper():<12} {adv_avg:<12.1f} {norm_avg:<12.1f} "
              f"{improvement:>+14.1f}% {cohens_d:<12.2f}")
    
    return results


def run_all_experiments(num_games_a: int = 30, num_games_b: int = 30):
    """Run both experiments with all configurations"""
    print_header("UROP3200: CHINESE POKER AI RESEARCH")
    print(f"\nStarting comprehensive experiment suite...")
    print(f"  Experiment A: {num_games_a} games per agent type")
    print(f"  Experiment B: {num_games_b} games per group")
    print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run experiments
    exp_a_results = run_experiment_a_all(num_games_a)
    exp_b_results = run_experiment_b_all(num_games_b)
    
    # Final summary
    print_header("RESEARCH FINDINGS SUMMARY")
    
    print("\n1. WIN RATE ANALYSIS (Experiment A)")
    print("   Testing if advanced features improve win rate...")
    for agent_type, result in exp_a_results.items():
        stats = result.agent_stats.get('高级玩家')
        if stats:
            baseline = 33.3  # Random baseline
            print(f"   • {agent_type.upper()}: {stats.win_rate:.1%} (baseline: {baseline:.1f}%, "
                  f"delta: {stats.win_rate*100 - baseline:+.1f}%)")
    
    print("\n2. EFFICIENCY ANALYSIS (Experiment B)")
    print("   Testing if advanced agents finish games faster...")
    import statistics
    for agent_type, (adv, norm) in exp_b_results.items():
        adv_avg = statistics.mean([r.turn_count for r in adv.results])
        norm_avg = statistics.mean([r.turn_count for r in norm.results])
        improvement = ((norm_avg - adv_avg) / norm_avg) * 100
        print(f"   • {agent_type.upper()}: {improvement:+.1f}% fewer turns "
              f"({norm_avg:.0f} → {adv_avg:.0f})")
    
    print("\n3. FEATURE COMPARISON")
    print("   Ranking of agent capabilities:")
    
    # Rank by win rate from Experiment A
    win_rates = []
    for agent_type, result in exp_a_results.items():
        stats = result.agent_stats.get('高级玩家')
        if stats:
            win_rates.append((agent_type, stats.win_rate))
    win_rates.sort(key=lambda x: x[1], reverse=True)
    
    for i, (agent_type, wr) in enumerate(win_rates, 1):
        print(f"   {i}. {agent_type.upper()} Agent: {wr:.1%} win rate")
    
    print(f"\n{'='*70}")
    print(f" Experiments completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Results saved in: ./results/")
    print(f"{'='*70}")
    
    return exp_a_results, exp_b_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Chinese Poker AI experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all experiments (full research suite)
  python run_experiments.py --all --num-games 30
  
  # Quick test (single game)
  python run_experiments.py --test
  
  # Experiment A only (1 advanced vs 2 normal)
  python run_experiments.py --exp-a --agent-type cot --num-games 20
  
  # Experiment B only (turn count comparison)
  python run_experiments.py --exp-b --advanced-type full --num-games 20
  
  # Run Experiment A with all agent types
  python run_experiments.py --exp-a --all-types --num-games 30
        """
    )
    
    parser.add_argument("--all", action="store_true",
                       help="Run complete experiment suite (A + B, all agent types)")
    parser.add_argument("--test", action="store_true",
                       help="Run single test game to verify setup")
    parser.add_argument("--exp-a", action="store_true",
                       help="Run Experiment A only")
    parser.add_argument("--exp-b", action="store_true",
                       help="Run Experiment B only")
    parser.add_argument("--agent-type", type=str, default="cot",
                       choices=["cot", "tool", "full"],
                       help="Agent type for Experiment A")
    parser.add_argument("--advanced-type", type=str, default="cot",
                       choices=["cot", "tool", "full"],
                       help="Agent type for Experiment B advanced group")
    parser.add_argument("--all-types", action="store_true",
                       help="Run with all agent types (cot, tool, full)")
    parser.add_argument("--num-games", type=int, default=30,
                       help="Number of games to run (default: 30)")
    
    args = parser.parse_args()
    
    # Default to --all if no arguments
    if not any([args.all, args.test, args.exp_a, args.exp_b]):
        print("No experiment specified. Use --all to run complete suite, or --help for options.")
        print("Running quick test by default...")
        args.test = True
    
    if args.test:
        run_single_game_test()
    
    elif args.all:
        run_all_experiments(args.num_games, args.num_games)
    
    elif args.exp_a:
        if args.all_types:
            run_experiment_a_all(args.num_games)
        else:
            run_experiment_a(args.agent_type, args.num_games)
    
    elif args.exp_b:
        if args.all_types:
            run_experiment_b_all(args.num_games)
        else:
            run_experiment_b(args.advanced_type, args.num_games)


if __name__ == "__main__":
    main()
