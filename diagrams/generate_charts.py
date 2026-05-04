#!/usr/bin/env python3
"""Generate performance comparison chart with Win Rate, Error Rate, and Average Turns.

Data is read directly from experiment result JSON files.
"""

import sys
import json
import traceback
from pathlib import Path

# Find the latest JSON files
def find_latest_result(results_dir, pattern):
    """Find the most recent result file matching pattern."""
    import glob
    files = glob.glob(str(results_dir / pattern))
    if not files:
        return None
    return max(files, key=lambda x: Path(x).stat().st_mtime)

def load_experiment_data():
    """Load experiment data from JSON files."""
    results_dir = Path('/Users/xuborong/Documents/GitHub/ChinesePokerAi/results')

    # Load each experiment's results
    data = {}

    # CoT Agent
    cot_file = find_latest_result(results_dir / 'experiment_a', 'Experiment_A_CoTAgent_vs_Normal_*.json')
    if cot_file:
        with open(cot_file) as f:
            d = json.load(f)
            stats = d['agent_stats']['玩家一']  # Advanced agent
            data['cot'] = {
                'win_rate': float(stats['win_rate'].rstrip('%')),
                'error_rate': float(stats['error_rate'].rstrip('%')),
                'avg_turns': float(stats['avg_turn_count'])
            }

    # ICL (Guide) Agent
    guide_file = find_latest_result(results_dir / 'experiment_a', 'Experiment_A_GuideAgent_vs_Normal_*.json')
    if guide_file:
        with open(guide_file) as f:
            d = json.load(f)
            stats = d['agent_stats']['玩家一']  # Advanced agent
            data['guide'] = {
                'win_rate': float(stats['win_rate'].rstrip('%')),
                'error_rate': float(stats['error_rate'].rstrip('%')),
                'avg_turns': float(stats['avg_turn_count'])
            }

    # Tool Agent
    tool_file = find_latest_result(results_dir / 'experiment_a', 'Experiment_A_ToolAgent_vs_Normal_*.json')
    if tool_file:
        with open(tool_file) as f:
            d = json.load(f)
            stats = d['agent_stats']['玩家一']  # Advanced agent
            data['tool'] = {
                'win_rate': float(stats['win_rate'].rstrip('%')),
                'error_rate': float(stats['error_rate'].rstrip('%')),
                'avg_turns': float(stats['avg_turn_count'])
            }

    # Baseline (3 Normal agents)
    baseline_file = find_latest_result(results_dir / 'baseline', 'Experiment_Baseline_3_Normal_Agents_*.json')
    if baseline_file:
        with open(baseline_file) as f:
            d = json.load(f)
            stats = d['agent_stats']['玩家一']  # Tracked baseline agent
            data['baseline'] = {
                'win_rate': float(stats['win_rate'].rstrip('%')),
                'error_rate': float(stats['error_rate'].rstrip('%')),
                'avg_turns': float(stats['avg_turn_count'])
            }

    return data

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    # Load data from JSON files
    data = load_experiment_data()

    print(f"Loaded data: {data}", file=sys.stderr)

    # Map to chart order: Chain-of-Thought, In-Context Learning, Tool-Augmented, Baseline
    agents = ['Chain-of-Thought', 'In-Context Learning', 'Tool-Augmented', 'Baseline']
    agent_keys = ['cot', 'guide', 'tool', 'baseline']

    win_rates = [data.get(k, {}).get('win_rate', 0) for k in agent_keys]
    error_rates = [data.get(k, {}).get('error_rate', 0) for k in agent_keys]
    avg_turns = [data.get(k, {}).get('avg_turns', 0) for k in agent_keys]

    print(f"Win rates: {win_rates}", file=sys.stderr)
    print(f"Error rates: {error_rates}", file=sys.stderr)
    print(f"Avg turns: {avg_turns}", file=sys.stderr)

    # Colors from mermaid fill colors (matching architectures_combined.mmd)
    colors = {
        'Chain-of-Thought': '#90caf9',  # Light blue
        'In-Context Learning': '#ffcc80',  # Light orange
        'Tool-Augmented': '#a5d6a7',  # Light green
        'Baseline': '#ef5350'  # Light red
    }

    agent_colors = [colors[a] for a in agents]

    # Create figure with 3 subplots (Win Rate, Error Rate, Average Turns)
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    # Common settings
    for ax in axes:
        ax.set_xticks(range(len(agents)))
        ax.set_xticklabels([a.replace('-', '-\n') for a in agents], rotation=0, ha='center', fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Subplot 1: Win Rate
    ax1 = axes[0]
    bars1 = ax1.bar(range(len(agents)), win_rates, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Win Rate (%)', fontweight='bold', fontsize=12)
    ax1.set_title('Win Rate\n(Higher is Better)', fontweight='bold', pad=10, fontsize=15)
    ax1.set_ylim(0, 100)
    ax1.tick_params(axis='y', labelsize=11)

    for i, (bar, val) in enumerate(zip(bars1, win_rates)):
        ax1.text(i, val + 2, f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

    # Subplot 2: Error Rate
    ax2 = axes[1]
    bars2 = ax2.bar(range(len(agents)), error_rates, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Error Rate (%)', fontweight='bold', fontsize=12)
    ax2.set_title('Error Rate\n(Lower is Better)', fontweight='bold', pad=10, fontsize=15)
    ax2.set_ylim(0, max(error_rates) * 1.2)
    ax2.tick_params(axis='y', labelsize=11)

    for i, (bar, val) in enumerate(zip(bars2, error_rates)):
        ax2.text(i, val + max(error_rates) * 0.03, f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

    # Subplot 3: Average Turns
    ax3 = axes[2]
    bars3 = ax3.bar(range(len(agents)), avg_turns, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Average Turns', fontweight='bold', fontsize=12)
    ax3.set_title('Average Turns\n(Lower is Better)', fontweight='bold', pad=10, fontsize=15)
    ax3.set_ylim(min(avg_turns) * 0.8, max(avg_turns) * 1.1)
    ax3.tick_params(axis='y', labelsize=11)

    for i, (bar, val) in enumerate(zip(bars3, avg_turns)):
        ax3.text(i, val + (max(avg_turns) - min(avg_turns)) * 0.02, f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=12)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[a], edgecolor='black', label=a) for a in agents]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.02),
              ncol=4, frameon=True, fontsize=12)

    # Main title
    fig.suptitle('Agent Performance Comparison: Win Rate, Error Rate, and Efficiency\n(Experiment A: 30 Games)',
                 fontsize=18, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    plt.savefig('/Users/xuborong/Documents/GitHub/ChinesePokerAi/diagrams/performance_comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Saved: performance_comparison.png", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
