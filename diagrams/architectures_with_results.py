#!/usr/bin/env python3
"""
Combined diagram showing all three agent architectures with performance results.
Similar to Mermaid but generated entirely with matplotlib.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

def draw_combined_diagram():
    """Draw combined architecture and results diagram."""
    fig = plt.figure(figsize=(18, 10))
    
    # Create grid spec for layout
    gs = fig.add_gridspec(2, 3, height_ratios=[3, 1], hspace=0.3, wspace=0.3)
    
    # Colors
    colors = {
        'cot': '#1565c0',
        'icl': '#ef6c00',
        'tool': '#2e7d32'
    }
    
    results = {
        'cot': {'win': 80.0, 'landlord': 90.0, 'farmer': 75.0, 'error': 50.9},
        'icl': {'win': 56.7, 'landlord': 20.0, 'farmer': 75.0, 'error': 193.5},
        'tool': {'win': 90.0, 'landlord': 100.0, 'farmer': 85.0, 'error': 37.9}
    }
    
    # === Row 1: Three Architecture Diagrams ===
    
    # 1. Chain-of-Thought
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 14)
    ax1.axis('off')
    ax1.set_title('Chain-of-Thought (CoT)', fontsize=13, fontweight='bold', 
                  color=colors['cot'], pad=10)
    
    # CoT boxes
    cot_boxes = [
        (5, 12.5, 'Prompt:\nGame State', '#e3f2fd'),
        (5, 10, 'LLM Model', '#bbdefb'),
        (5, 6.5, 'Step-by-Step Reasoning:\n• Situation Analysis\n• Option Evaluation\n• Risk Assessment', '#90caf9'),
        (5, 2.5, 'Final Decision', '#64b5f6'),
        (5, 0.5, 'Response:\nCards / PASS', '#42a5f5')
    ]
    
    for i, (x, y, text, color) in enumerate(cot_boxes):
        height = 1.8 if i == 2 else 1.2
        box = FancyBboxPatch((x-2, y-height/2), 4, height, boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor=colors['cot'], linewidth=2)
        ax1.add_patch(box)
        ax1.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')
        if i < len(cot_boxes) - 1:
            next_y = cot_boxes[i+1][1] + (1.8 if i+1 == 2 else 1.2)/2
            ax1.annotate('', xy=(x, y - height/2 - 0.1), xytext=(x, next_y + 0.1),
                        arrowprops=dict(arrowstyle='->', color=colors['cot'], lw=2))
    
    # 2. In-Context Learning
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 14)
    ax2.axis('off')
    ax2.set_title('In-Context Learning', fontsize=13, fontweight='bold',
                  color=colors['icl'], pad=10)
    
    # ICL boxes - side by side merging
    box_guide = FancyBboxPatch((0.5, 11), 3.5, 1.5, boxstyle="round,pad=0.05",
                              facecolor='#ffe0b2', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box_guide)
    ax2.text(2.25, 11.75, 'Strategy Guide', ha='center', va='center', fontsize=9, fontweight='bold')
    
    box_prompt = FancyBboxPatch((6, 11), 3.5, 1.5, boxstyle="round,pad=0.05",
                               facecolor='#fff3e0', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box_prompt)
    ax2.text(7.75, 11.75, 'Prompt:\nGame State', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Merge arrows
    ax2.annotate('', xy=(5, 9.5), xytext=(2.25, 10.9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    ax2.annotate('', xy=(5, 9.5), xytext=(7.75, 10.9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # Merge point
    merge = FancyBboxPatch((3, 8.5), 4, 1.2, boxstyle="round,pad=0.05",
                          facecolor='#ffcc80', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(merge)
    ax2.text(5, 9.1, 'Concatenate', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # LLM and output
    icl_boxes = [
        (5, 6, 'LLM Model', '#ffe0b2'),
        (5, 3.5, 'Response:\nCards / PASS', '#fff3e0')
    ]
    
    for i, (x, y, text, color) in enumerate(icl_boxes):
        box = FancyBboxPatch((x-2, y-0.6), 4, 1.2, boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor=colors['icl'], linewidth=2)
        ax2.add_patch(box)
        ax2.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
        if i == 0:
            ax2.annotate('', xy=(x, y-0.7), xytext=(x, y-0.9),
                        arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # 3. Tool-Augmented
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 14)
    ax3.axis('off')
    ax3.set_title('Tool-Augmented (Parallel)', fontsize=13, fontweight='bold',
                  color=colors['tool'], pad=10)
    
    # Input
    box_in = FancyBboxPatch((3, 12.5), 4, 1, boxstyle="round,pad=0.05",
                           facecolor='#e8f5e9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_in)
    ax3.text(5, 13, 'Prompt: Game State', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # LLM Decision
    box_decide = FancyBboxPatch((3, 10.5), 4, 1, boxstyle="round,pad=0.05",
                               facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_decide)
    ax3.text(5, 11, 'LLM (Decision)', ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax3.annotate('', xy=(5, 10.4), xytext=(5, 12.4),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Decision diamond
    diamond = plt.Polygon([(5, 8.5), (6.5, 7.5), (5, 6.5), (3.5, 7.5)],
                          facecolor='#a5d6a7', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(diamond)
    ax3.text(5, 7.5, 'Need\nTools?', ha='center', va='center', fontsize=8, fontweight='bold')
    
    ax3.annotate('', xy=(5, 8.6), xytext=(5, 10.4),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Tool boxes - horizontal
    tool_y = 5
    tool_names = ['Recommend', 'Best Play', 'Valid Moves']
    tool_x = [1.5, 5, 8.5]
    
    for x, name in zip(tool_x, tool_names):
        box = FancyBboxPatch((x-1.2, tool_y-0.5), 2.4, 1, boxstyle="round,pad=0.05",
                            facecolor='#81c784', edgecolor=colors['tool'], linewidth=2)
        ax3.add_patch(box)
        ax3.text(x, tool_y, name, ha='center', va='center', fontsize=8, fontweight='bold')
        # Arrows from decision to tools
        ax3.annotate('', xy=(x, tool_y+0.6), xytext=(5, 6.4),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Tool results
    results_box = FancyBboxPatch((3, 3), 4, 1, boxstyle="round,pad=0.05",
                               facecolor='#66bb6a', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(results_box)
    ax3.text(5, 3.5, 'Combined Tool Results', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows from tools to results
    for x in tool_x:
        ax3.annotate('', xy=(5, 4.1), xytext=(x, 4.4),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Final LLM
    box_final = FancyBboxPatch((3, 1), 4, 1, boxstyle="round,pad=0.05",
                              facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_final)
    ax3.text(5, 1.5, 'LLM (Final Decision)', ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax3.annotate('', xy=(5, 2.9), xytext=(5, 3),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # === Row 2: Results Charts ===
    
    # 1. CoT Results
    ax4 = fig.add_subplot(gs[1, 0])
    metrics = ['Win\nRate', 'Landlord', 'Farmer', 'Error\nRate']
    values = [80.0, 90.0, 75.0, 50.9]
    bar_colors = ['#42a5f5', '#90caf9', '#90caf9', '#ef5350']
    
    bars = ax4.bar(range(len(metrics)), values, color=bar_colors, edgecolor=colors['cot'], linewidth=2)
    ax4.set_xticks(range(len(metrics)))
    ax4.set_xticklabels(metrics, fontsize=9)
    ax4.set_ylim(0, 100)
    ax4.set_title('CoT Performance Metrics', fontsize=11, fontweight='bold', color=colors['cot'])
    ax4.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar, val in zip(bars, values):
        ax4.text(bar.get_x() + bar.get_width()/2., val + 2, f'{val:.1f}%',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 2. ICL Results
    ax5 = fig.add_subplot(gs[1, 1])
    values_icl = [56.7, 20.0, 75.0, 50.0]  # Scale error for display
    bar_colors_icl = ['#ffa726', '#ffcc80', '#ffcc80', '#ef5350']
    
    bars = ax5.bar(range(len(metrics)), values_icl, color=bar_colors_icl, 
                   edgecolor=colors['icl'], linewidth=2)
    ax5.set_xticks(range(len(metrics)))
    ax5.set_xticklabels(metrics, fontsize=9)
    ax5.set_ylim(0, 100)
    ax5.set_title('ICL Performance Metrics', fontsize=11, fontweight='bold', color=colors['icl'])
    ax5.grid(axis='y', alpha=0.3, linestyle='--')
    
    labels_icl = ['56.7%', '20.0%', '75.0%', '193.5%']
    for bar, val, label in zip(bars, values_icl, labels_icl):
        ax5.text(bar.get_x() + bar.get_width()/2., min(val + 2, 95), label,
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # 3. Tool Results
    ax6 = fig.add_subplot(gs[1, 2])
    values_tool = [90.0, 100.0, 85.0, 37.9]
    bar_colors_tool = ['#66bb6a', '#a5d6a7', '#a5d6a7', '#ef5350']
    
    bars = ax6.bar(range(len(metrics)), values_tool, color=bar_colors_tool,
                   edgecolor=colors['tool'], linewidth=2)
    ax6.set_xticks(range(len(metrics)))
    ax6.set_xticklabels(metrics, fontsize=9)
    ax6.set_ylim(0, 110)
    ax6.set_title('Tool Performance Metrics', fontsize=11, fontweight='bold', color=colors['tool'])
    ax6.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar, val in zip(bars, values_tool):
        ax6.text(bar.get_x() + bar.get_width()/2., val + 2, f'{val:.1f}%',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Main title
    fig.suptitle('LLM Agent Architectures: Workflow and Performance Comparison\n(Experiment A: 30 Games, 1 Advanced vs 2 Baseline Agents)',
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.savefig('/Users/xuborong/Documents/GitHub/ChinesePokerAi/diagrams/architectures_combined.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Saved: architectures_combined.png")
    plt.close()

if __name__ == "__main__":
    draw_combined_diagram()
