"""
Experiment A: 1 Advanced Agent vs 2 Normal Agents
Tests whether advanced features improve win rate.
"""

import sys
sys.path.insert(0, '/Users/xuborong/Documents/GitHub/ChinesePokerAi')

from ai_agent import CoTAgent, ToolAgent, FullAgent, NormalAgent, AgentConfig, load_strategy_guide
from evaluation import Evaluator


def run_experiment_a(agent_type: str = "cot", num_games: int = 30):
    """
    Run Experiment A with specified advanced agent type.
    
    Args:
        agent_type: "cot", "tool", or "full"
        num_games: Number of games to run (default 30)
    """
    print("=" * 60)
    print("EXPERIMENT A: 1 Advanced Agent vs 2 Normal Agents")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  - Player 1: {agent_type.upper()} Agent (Advanced)")
    print(f"  - Player 2: Normal Agent")
    print(f"  - Player 3: Normal Agent")
    print(f"  - Games: {num_games}")
    print(f"  - Landlord rotation: Yes (each player gets equal turns as landlord)")
    
    # Create evaluator
    evaluator = Evaluator(output_dir="results/experiment_a")
    
    # Create advanced agent
    config = AgentConfig(use_cot=True, use_tools=True, use_guide=True)
    
    if agent_type == "cot":
        advanced_agent = CoTAgent("高级玩家", config)
    elif agent_type == "tool":
        advanced_agent = ToolAgent("高级玩家", config)
    elif agent_type == "full":
        guide = load_strategy_guide("guides/advanced_guide.md")
        advanced_agent = FullAgent("高级玩家", config, guide_content=guide)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Normal agent factory
    def normal_agent_factory():
        return NormalAgent("普通玩家", AgentConfig())
    
    # Run experiment
    result = evaluator.evaluate_experiment_a(
        advanced_agent=advanced_agent,
        normal_agent_factory=normal_agent_factory,
        num_games=num_games
    )
    
    # Additional analysis
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    
    # Extract win rates
    for name, stats in result.agent_stats.items():
        if stats.agent_type == "advanced":
            print(f"\nAdvanced Agent ({agent_type.upper()}):")
            print(f"  Overall win rate: {stats.win_rate:.1%}")
            print(f"  As landlord: {stats.wins_as_landlord}/{stats.games_as_landlord} ({stats.wins_as_landlord/max(1,stats.games_as_landlord):.1%})")
            print(f"  As farmer: {stats.wins_as_farmer}/{stats.games_as_farmer} ({stats.wins_as_farmer/max(1,stats.games_as_farmer):.1%})")
        else:
            print(f"\nNormal Agent ({name}):")
            print(f"  Overall win rate: {stats.win_rate:.1%}")
    
    print(f"\nConclusion: Advanced agent ({agent_type.upper()}) achieved "
          f"{result.agent_stats.get('高级玩家', AgentStats('','')).win_rate:.1%} win rate "
          f"vs normal agents' ~{sum(s.win_rate for n,s in result.agent_stats.items() if s.agent_type=='normal')/2:.1%} average")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Experiment A")
    parser.add_argument("--agent-type", type=str, default="cot",
                       choices=["cot", "tool", "full"],
                       help="Type of advanced agent")
    parser.add_argument("--num-games", type=int, default=30,
                       help="Number of games to run")
    parser.add_argument("--all", action="store_true",
                       help="Run all agent types")
    
    args = parser.parse_args()
    
    from evaluation import AgentStats
    
    if args.all:
        results = {}
        for agent_type in ["cot", "tool", "full"]:
            print(f"\n\n{'='*60}")
            print(f"Running with {agent_type.upper()} agent...")
            print(f"{'='*60}")
            result = run_experiment_a(agent_type, args.num_games)
            results[agent_type] = result
        
        # Compare all
        print("\n\n" + "=" * 60)
        print("COMPARISON: All Advanced Agent Types")
        print("=" * 60)
        for agent_type, result in results.items():
            stats = result.agent_stats.get('高级玩家', AgentStats('', ''))
            print(f"\n{agent_type.upper()}:")
            print(f"  Win rate: {stats.win_rate:.1%}")
            print(f"  Avg turns: {stats.avg_turn_count:.1f}")
            print(f"  Error rate: {stats.error_rate:.2%}")
    else:
        run_experiment_a(args.agent_type, args.num_games)
