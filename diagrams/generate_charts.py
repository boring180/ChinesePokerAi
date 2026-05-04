#!/usr/bin/env python3
"""Generate performance comparison chart with Win Rate, Error Rate, and Average Turns."""

import sys
import traceback

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    # Data - matching mermaid colors
    agents = ['Chain-of-Thought', 'In-Context Learning', 'Tool-Augmented', 'Baseline']
    win_rates = [80.0, 56.7, 90.0, 33.3]
    error_rates = [50.9, 193.5, 37.9, 193.5]
    avg_turns = [48.7, 60.7, 51.0, 60.7]

    # Colors from mermaid fill colors (matching architectures_combined.mmd)
    colors = {
        'Chain-of-Thought': '#90caf9',  # Light blue (from #e3f2fd fill, using slightly darker for visibility)
        'In-Context Learning': '#ffcc80',  # Light orange (from #fff3e0 fill)
        'Tool-Augmented': '#a5d6a7',  # Light green (from #e8f5e9 fill)
        'Baseline': '#ef5350'  # Light red
    }
    
    agent_colors = [colors[a] for a in agents]

    # Create figure with 3 subplots (Win Rate, Error Rate, Average Turns)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Common settings
    for ax in axes:
        ax.set_xticks(range(len(agents)))
        ax.set_xticklabels([a.replace('-', '-\n') for a in agents], rotation=0, ha='center', fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Subplot 1: Win Rate
    ax1 = axes[0]
    bars1 = ax1.bar(range(len(agents)), win_rates, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Win Rate (%)', fontweight='bold')
    ax1.set_title('Win Rate\n(Higher is Better)', fontweight='bold', pad=10)
    ax1.set_ylim(0, 100)
    
    for i, (bar, val) in enumerate(zip(bars1, win_rates)):
        ax1.text(i, val + 2, f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Subplot 2: Error Rate
    ax2 = axes[1]
    bars2 = ax2.bar(range(len(agents)), error_rates, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Error Rate (%)', fontweight='bold')
    ax2.set_title('Error Rate\n(Lower is Better)', fontweight='bold', pad=10)
    ax2.set_ylim(0, 220)
    
    for i, (bar, val) in enumerate(zip(bars2, error_rates)):
        ax2.text(i, val + 5, f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Subplot 3: Average Turns
    ax3 = axes[2]
    bars3 = ax3.bar(range(len(agents)), avg_turns, color=agent_colors, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Average Turns', fontweight='bold')
    ax3.set_title('Average Turns\n(Lower is Better)', fontweight='bold', pad=10)
    ax3.set_ylim(40, 70)
    
    for i, (bar, val) in enumerate(zip(bars3, avg_turns)):
        ax3.text(i, val + 1, f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[a], edgecolor='black', label=a) for a in agents]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.02), 
              ncol=4, frameon=True, fontsize=10)
    
    # Main title
    fig.suptitle('Agent Performance Comparison: Win Rate, Error Rate, and Efficiency\n(Experiment A: 30 Games)', 
                 fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    plt.savefig('/Users/xuborong/Documents/GitHub/ChinesePokerAi/diagrams/performance_comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Saved: performance_comparison.png", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
