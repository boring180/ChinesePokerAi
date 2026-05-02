"""
Experiment B: 3 Advanced Agents vs 3 Normal Agents
Compares turn count (efficiency) between groups.
"""

import sys
sys.path.insert(0, '/Users/xuborong/Documents/GitHub/ChinesePokerAi')

from ai_agent import GuideAgent, CoTAgent, ToolAgent, FullAgent, NormalAgent, AgentConfig, load_strategy_guide
from evaluation import Evaluator


def run_experiment_b(advanced_type: str = "cot", num_games: int = 30):
    """
    Run Experiment B comparing turn counts.
    
    Args:
        advanced_type: "guide", "cot", "tool", or "full"
        num_games: Number of games per group (default 30)
    """
    print("=" * 60)
    print("EXPERIMENT B: Turn Count Comparison")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  - Group 1: 3 {advanced_type.upper()} Agents")
    print(f"  - Group 2: 3 Normal Agents")
    print(f"  - Games per group: {num_games}")
    print(f"  - Metric: Average turn count (lower is more efficient)")
    
    # Create evaluator
    evaluator = Evaluator(output_dir="results/experiment_b")
    
    # Load guide for full agents
    guide = load_strategy_guide("guides/advanced_guide.md")
    
    # Advanced agent factory
    def advanced_factory(name):
        if advanced_type == "guide":
            return GuideAgent(name, guide_content=guide, config=AgentConfig(use_guide=True))
        config = AgentConfig(use_cot=True, use_tools=True, use_guide=True)
        if advanced_type == "cot":
            return CoTAgent(name, config)
        elif advanced_type == "tool":
            return ToolAgent(name, config)
        elif advanced_type == "full":
            return FullAgent(name, config, guide_content=guide)
        else:
            raise ValueError(f"Unknown agent type: {advanced_type}")
    
    # Normal agent factory
    def normal_factory(name):
        return NormalAgent(name, AgentConfig())
    
    # Run experiment
    result_advanced, result_normal = evaluator.evaluate_experiment_b(
        advanced_agent_factory=advanced_factory,
        normal_agent_factory=normal_factory,
        num_games=num_games
    )
    
    # Statistical significance (basic)
    print("\n" + "=" * 60)
    print("STATISTICAL SUMMARY")
    print("=" * 60)
    
    adv_turns = [r.turn_count for r in result_advanced.results]
    norm_turns = [r.turn_count for r in result_normal.results]
    
    import statistics
    
    print(f"\n{advanced_type.upper()} Agents Group:")
    print(f"  Mean turns: {statistics.mean(adv_turns):.1f}")
    print(f"  Std dev: {statistics.stdev(adv_turns):.1f}")
    print(f"  Min: {min(adv_turns)}, Max: {max(adv_turns)}")
    
    print(f"\nNormal Agents Group:")
    print(f"  Mean turns: {statistics.mean(norm_turns):.1f}")
    print(f"  Std dev: {statistics.stdev(norm_turns):.1f}")
    print(f"  Min: {min(norm_turns)}, Max: {max(norm_turns)}")
    
    # Effect size
    mean_diff = statistics.mean(norm_turns) - statistics.mean(adv_turns)
    pooled_std = ((statistics.stdev(adv_turns)**2 + statistics.stdev(norm_turns)**2) / 2) ** 0.5
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
    
    print(f"\nEffect Size (Cohen's d): {cohens_d:.2f}")
    if abs(cohens_d) < 0.2:
        effect = "negligible"
    elif abs(cohens_d) < 0.5:
        effect = "small"
    elif abs(cohens_d) < 0.8:
        effect = "medium"
    else:
        effect = "large"
    print(f"Interpretation: {effect} effect")
    
    return result_advanced, result_normal


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Experiment B")
    parser.add_argument("--advanced-type", type=str, default="cot",
                       choices=["guide", "cot", "tool", "full"],
                       help="Type of advanced agent")
    parser.add_argument("--num-games", type=int, default=30,
                       help="Number of games per group")
    parser.add_argument("--all", action="store_true",
                       help="Run all advanced agent types")
    
    args = parser.parse_args()
    
    if args.all:
        results = {}
        for agent_type in ["guide", "cot", "tool", "full"]:
            print(f"\n\n{'='*60}")
            print(f"Running with {agent_type.upper()} agents...")
            print(f"{'='*60}")
            adv_result, norm_result = run_experiment_b(agent_type, args.num_games)
            results[agent_type] = (adv_result, norm_result)
        
        # Summary comparison
        print("\n\n" + "=" * 60)
        print("FINAL COMPARISON: All Agent Types")
        print("=" * 60)
        print(f"\n{'Agent Type':<12} {'Adv Avg Turns':<15} {'Norm Avg Turns':<15} {'Improvement'}")
        print("-" * 60)
        
        import statistics
        for agent_type, (adv, norm) in results.items():
            adv_avg = statistics.mean([r.turn_count for r in adv.results])
            norm_avg = statistics.mean([r.turn_count for r in norm.results])
            improvement = ((norm_avg - adv_avg) / norm_avg) * 100
            print(f"{agent_type.upper():<12} {adv_avg:<15.1f} {norm_avg:<15.1f} {improvement:+.1f}%")
    else:
        run_experiment_b(args.advanced_type, args.num_games)
