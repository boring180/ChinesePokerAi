"""
Chinese Poker AI - Main Entry Point
UROP3200 Research Project: AI Agents Playing Dou Di Zhu

Usage:
    python AI_game_play.py                    # Quick test
    python AI_game_play.py --exp-a            # Run Experiment A
    python AI_game_play.py --exp-b            # Run Experiment B
    python AI_game_play.py --all              # Run all experiments
    python AI_game_play.py --demo             # Run demo game with verbose output
"""

import argparse
import sys

def print_banner():
    """Print project banner"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              斗地主 AI 研究项目 (UROP3200)                         ║
║         Chinese Poker (Dou Di Zhu) AI Research                    ║
╚══════════════════════════════════════════════════════════════════╝

研究内容:
  • Chain-of-Thought (CoT) 推理
  • Tool Calling (工具调用)
  • Strategy Guide Integration (策略指南)
  • Multi-Agent Comparison (多智能体对比)

实验设计:
  Experiment A: 1个高级AI vs 2个普通AI (胜率对比)
  Experiment B: 3个高级AI vs 3个普通AI (回合数对比)
""")


def run_demo():
    """Run a single demo game with verbose output"""
    print("\n" + "="*60)
    print("DEMO MODE: Single Game with Verbose Output")
    print("="*60 + "\n")
    
    from game_runner import GameRunner
    from ai_agent import NormalAgent, AgentConfig
    
    # Create agents
    agents = [
        NormalAgent("地主AI", AgentConfig()),
        NormalAgent("农民1", AgentConfig()),
        NormalAgent("农民2", AgentConfig()),
    ]
    
    # Run game with full output
    runner = GameRunner(agents, verbose=True, enable_logging=True)
    result = runner.run_game(random_landlord=True)
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print(f"Winner: {result.winner_name} ({result.winner_role})")
    print(f"Total turns: {result.turn_count}")
    print(f"Errors: {result.error_count}")
    print(f"Log saved to: game_log_*.txt")


def main():
    """Main entry point"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Chinese Poker AI Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument("--demo", action="store_true",
                       help="Run a single demo game with verbose output")
    parser.add_argument("--exp-a", action="store_true",
                       help="Run Experiment A: 1 Advanced vs 2 Normal")
    parser.add_argument("--exp-b", action="store_true",
                       help="Run Experiment B: Turn Count Comparison")
    parser.add_argument("--all", action="store_true",
                       help="Run complete experiment suite")
    parser.add_argument("--quick-test", action="store_true",
                       help="Quick test (1 game, no output)")
    parser.add_argument("--agent-type", type=str, default="cot",
                       choices=["normal", "guide", "cot", "tool", "full"],
                       help="Agent type for experiments")
    parser.add_argument("--num-games", type=int, default=30,
                       help="Number of games to run")
    
    args = parser.parse_args()
    
    # Default to demo if no args
    if not any([args.demo, args.exp_a, args.exp_b, args.all, args.quick_test]):
        print("\nNo mode specified. Running demo game...")
        print("Use --help to see all options.\n")
        run_demo()
        return
    
    if args.demo:
        run_demo()
    
    elif args.quick_test:
        print("\nRunning quick test...")
        from evaluation import quick_test
        quick_test(["normal", "normal", "normal"], num_games=1)
    
    elif args.exp_a:
        from experiments.experiment_a import run_experiment_a
        print(f"\nRunning Experiment A with {args.agent_type} agent...")
        run_experiment_a(args.agent_type, args.num_games)
    
    elif args.exp_b:
        from experiments.experiment_b import run_experiment_b
        print(f"\nRunning Experiment B with {args.agent_type} agents...")
        run_experiment_b(args.agent_type, args.num_games)
    
    elif args.all:
        from run_experiments import run_all_experiments
        print("\nRunning complete experiment suite...")
        run_all_experiments(args.num_games, args.num_games)
    
    print("\n" + "="*60)
    print("Thank you for using Chinese Poker AI!")
    print("="*60)


if __name__ == "__main__":
    main()
