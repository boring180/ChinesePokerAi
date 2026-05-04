#!/usr/bin/env python3
"""
Generate horizontal layout architecture diagrams.
Three subgraphs side by side with top-to-bottom flow in each.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def draw_horizontal_architectures():
    """Draw three architectures horizontally with same dimensions."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    
    # Colors
    colors = {
        'cot': '#1565c0',
        'icl': '#ef6c00',
        'tool': '#2e7d32'
    }
    
    # Common settings for all subplots
    for ax in axes:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 12)
        ax.axis('off')
    
    # === Subplot 1: Chain-of-Thought (Left) ===
    ax1 = axes[0]
    ax1.set_title('Chain-of-Thought (CoT)', fontsize=14, fontweight='bold', 
                  color=colors['cot'], pad=15)
    
    # CoT boxes - vertical arrangement
    cot_elements = [
        (5, 10.5, 'Prompt:\nGame State', '#e3f2fd', 2.5, 1.0),
        (5, 8.8, 'LLM Model', '#bbdefb', 2.5, 0.8),
        (5, 6.5, 'Step-by-Step Reasoning', '#90caf9', 2.8, 0.8),
        (5, 5.2, '• Situation Analysis', '#90caf9', 2.8, 0.6),
        (5, 4.4, '• Option Evaluation', '#90caf9', 2.8, 0.6),
        (5, 3.6, '• Risk Assessment', '#90caf9', 2.8, 0.6),
        (5, 2.0, 'Final Decision', '#64b5f6', 2.5, 0.8),
        (5, 0.5, 'Response:\nCards / PASS', '#42a5f5', 2.5, 0.8),
    ]
    
    for i, (x, y, text, color, w, h) in enumerate(cot_elements):
        box = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor=colors['cot'], linewidth=2)
        ax1.add_patch(box)
        ax1.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
        if i < len(cot_elements) - 1:
            ax1.annotate('', xy=(x, y-cot_elements[i][5]/2-0.1), 
                        xytext=(x, y+cot_elements[i][5]/2+0.1),
                        arrowprops=dict(arrowstyle='->', color=colors['cot'], lw=2))
    
    # === Subplot 2: In-Context Learning (Center) ===
    ax2 = axes[1]
    ax2.set_title('In-Context Learning', fontsize=14, fontweight='bold',
                  color=colors['icl'], pad=15)
    
    # ICL boxes - vertical with merge
    # Side inputs merging
    box_guide = FancyBboxPatch((1.5, 10), 3, 1.2, boxstyle="round,pad=0.05",
                              facecolor='#ffe0b2', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box_guide)
    ax2.text(3, 10.6, 'Strategy Guide', ha='center', va='center', fontsize=10, fontweight='bold')
    
    box_prompt = FancyBboxPatch((6.5, 10), 3, 1.2, boxstyle="round,pad=0.05",
                               facecolor='#fff3e0', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box_prompt)
    ax2.text(8, 10.6, 'Prompt:\nGame State', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Merge arrows
    ax2.annotate('', xy=(5, 8.8), xytext=(3, 9.9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    ax2.annotate('', xy=(5, 8.8), xytext=(8, 9.9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # Merge point
    merge = FancyBboxPatch((3, 7.8), 4, 0.8, boxstyle="round,pad=0.05",
                          facecolor='#ffcc80', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(merge)
    ax2.text(5, 8.2, 'Concatenate', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Continue vertical
    icl_elements = [
        (5, 6.5, 'LLM Model', '#ffe0b2', 3.5, 0.8),
        (5, 4.5, 'Response:\nCards / PASS', '#fff3e0', 3.5, 0.8),
    ]
    
    for x, y, text, color, w, h in icl_elements:
        box = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor=colors['icl'], linewidth=2)
        ax2.add_patch(box)
        ax2.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax2.annotate('', xy=(5, 7.3), xytext=(5, 7.7),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    ax2.annotate('', xy=(5, 5.9), xytext=(5, 6.1),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # === Subplot 3: Tool-Augmented (Right) ===
    ax3 = axes[2]
    ax3.set_title('Tool-Augmented (Parallel)', fontsize=14, fontweight='bold',
                  color=colors['tool'], pad=15)
    
    # Tool boxes - vertical with parallel tools
    t_input = FancyBboxPatch((3, 10.5), 4, 0.8, boxstyle="round,pad=0.05",
                           facecolor='#e8f5e9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(t_input)
    ax3.text(5, 10.9, 'Prompt: Game State', ha='center', va='center', fontsize=10, fontweight='bold')
    
    t_llm1 = FancyBboxPatch((3, 9, 4, 0.8), boxstyle="round,pad=0.05",
                           facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(t_llm1)
    ax3.text(5, 9.4, 'LLM (Decision)', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax3.annotate('', xy=(5, 9.4), xytext=(5, 10.4),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Decision diamond
    diamond = plt.Polygon([(5, 8), (6, 7.2), (5, 6.4), (4, 7.2)],
                          facecolor='#a5d6a7', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(diamond)
    ax3.text(5, 7.2, 'Need\nTools?', ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax3.annotate('', xy=(5, 8), xytext=(5, 8.9),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Three parallel tool boxes
    tool_y = 5.2
    tools = [
        (1.8, 'Get\nRecommend'),
        (5, 'Find\nBest Play'),
        (8.2, 'Valid\nMoves')
    ]
    
    for x, name in tools:
        box = FancyBboxPatch((x-1.3, tool_y-0.5), 2.6, 1, boxstyle="round,pad=0.05",
                            facecolor='#81c784', edgecolor=colors['tool'], linewidth=2)
        ax3.add_patch(box)
        ax3.text(x, tool_y, name, ha='center', va='center', fontsize=9, fontweight='bold')
        # Arrow from decision
        ax3.annotate('', xy=(x, tool_y+0.6), xytext=(4.3 if x < 3 else 5.7, 6.4),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Tool results
    t_results = FancyBboxPatch((3, 3.5), 4, 0.8, boxstyle="round,pad=0.05",
                              facecolor='#66bb6a', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(t_results)
    ax3.text(5, 3.9, 'Tool Results', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Arrows to results
    for x, _ in tools:
        ax3.annotate('', xy=(5, 4.4), xytext=(x, 4.7),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Final LLM
    t_llm2 = FancyBboxPatch((3, 2), 4, 0.8, boxstyle="round,pad=0.05",
                           facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(t_llm2)
    ax3.text(5, 2.4, 'LLM (Final)', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax3.annotate('', xy=(5, 2.5), xytext=(5, 3.4),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Output
    t_output = FancyBboxPatch((3, 0.5), 4, 0.8, boxstyle="round,pad=0.05",
                             facecolor='#e8f5e9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(t_output)
    ax3.text(5, 0.9, 'Response: Cards / PASS', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax3.annotate('', xy=(5, 1.0), xytext=(5, 1.5),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Main title
    fig.suptitle('LLM Agent Architectures for Multi-Agent Coordination', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig('/Users/xuborong/Documents/GitHub/ChinesePokerAi/diagrams/architectures_horizontal.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Saved: architectures_horizontal.png")
    plt.close()

if __name__ == "__main__":
    draw_horizontal_architectures()
