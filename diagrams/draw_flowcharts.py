#!/usr/bin/env python3
"""Draw flowchart-style diagrams using matplotlib - no external tools needed."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def draw_flowchart():
    """Draw a flowchart comparing the three agent architectures."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 8))
    
    # Colors for each architecture
    colors = {
        'cot': '#1565c0',
        'icl': '#ef6c00', 
        'tool': '#2e7d32'
    }
    
    # === Subplot 1: Chain-of-Thought ===
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 12)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('Chain-of-Thought (CoT)', 
                  fontsize=14, fontweight='bold', color=colors['cot'], pad=20)
    
    # Draw boxes
    boxes_cot = [
        (5, 10.5, 'Prompt:\nGame State'),
        (5, 8.5, 'LLM\nModel'),
        (5, 5.5, 'Step-by-Step\nReasoning:\n1. Analysis\n2. Evaluation\n3. Assessment'),
        (5, 2.5, 'Final\nDecision'),
        (5, 0.8, 'Response:\nCards/PASS')
    ]
    
    for i, (x, y, text) in enumerate(boxes_cot):
        color = '#e3f2fd' if i in [0, 4] else '#bbdefb' if i == 1 else '#90caf9'
        box = FancyBboxPatch((x-1.8, y-0.7), 3.6, 1.4 if i != 2 else 3,
                            boxstyle="round,pad=0.1", 
                            facecolor=color, edgecolor=colors['cot'], linewidth=2)
        ax1.add_patch(box)
        ax1.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
        if i < len(boxes_cot) - 1:
            ax1.annotate('', xy=(x, y-0.9 if i != 1 else y-2.2), xytext=(x, y-1.5 if i != 1 else y-2.8),
                        arrowprops=dict(arrowstyle='->', color=colors['cot'], lw=2))
    
    # === Subplot 2: In-Context Learning ===
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 12)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('In-Context Learning',
                  fontsize=14, fontweight='bold', color=colors['icl'], pad=20)
    
    # Strategy Guide and Prompt merge
    box1 = FancyBboxPatch((1.5, 9), 2.5, 1.2, boxstyle="round,pad=0.1",
                         facecolor='#ffe0b2', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box1)
    ax2.text(2.75, 9.6, 'Strategy\nGuide', ha='center', va='center', fontsize=9, fontweight='bold')
    
    box2 = FancyBboxPatch((6, 9), 2.5, 1.2, boxstyle="round,pad=0.1",
                         facecolor='#fff3e0', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(box2)
    ax2.text(7.25, 9.6, 'Prompt:\nGame State', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Merge arrow
    ax2.annotate('', xy=(5, 7.5), xytext=(2.75, 9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    ax2.annotate('', xy=(5, 7.5), xytext=(7.25, 9),
                arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # Merge box
    merge_box = FancyBboxPatch((3, 6.5), 4, 1.2, boxstyle="round,pad=0.1",
                              facecolor='#ffcc80', edgecolor=colors['icl'], linewidth=2)
    ax2.add_patch(merge_box)
    ax2.text(5, 7.1, 'Concatenate\nGuide + Prompt', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # LLM and Response
    boxes_icl = [
        (5, 4.5, 'LLM\nModel'),
        (5, 2.5, 'Response:\nCards/PASS')
    ]
    
    for i, (x, y, text) in enumerate(boxes_icl):
        color = '#ffe0b2' if i == 0 else '#fff3e0'
        box = FancyBboxPatch((x-1.8, y-0.6), 3.6, 1.2,
                            boxstyle="round,pad=0.1",
                            facecolor=color, edgecolor=colors['icl'], linewidth=2)
        ax2.add_patch(box)
        ax2.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
        if i == 0:
            ax2.annotate('', xy=(x, y-0.8), xytext=(x, y-1.3),
                        arrowprops=dict(arrowstyle='->', color=colors['icl'], lw=2))
    
    # === Subplot 3: Tool-Augmented ===
    ax3 = axes[2]
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 12)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('Tool-Augmented (Parallel)',
                  fontsize=14, fontweight='bold', color=colors['tool'], pad=20)
    
    # Input and LLM decision
    box_in = FancyBboxPatch((3.5, 10.5), 3, 1, boxstyle="round,pad=0.1",
                           facecolor='#e8f5e9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_in)
    ax3.text(5, 11, 'Prompt: Game State', ha='center', va='center', fontsize=9, fontweight='bold')
    
    box_llm1 = FancyBboxPatch((3.5, 8.8), 3, 1, boxstyle="round,pad=0.1",
                             facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_llm1)
    ax3.text(5, 9.3, 'LLM Model\n(Decision)', ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax3.annotate('', xy=(5, 8.7), xytext=(5, 10.4),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Decision diamond
    diamond = plt.Polygon([(5, 7.5), (6.5, 6.5), (5, 5.5), (3.5, 6.5)],
                          facecolor='#a5d6a7', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(diamond)
    ax3.text(5, 6.5, 'Need\nTools?', ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Tool boxes
    tool_boxes = [
        (1.5, 4, 'Get\nRecommendations'),
        (5, 4, 'Find\nBest Play'),
        (8.5, 4, 'Valid\nMoves')
    ]
    
    for i, (x, y, text) in enumerate(tool_boxes):
        box = FancyBboxPatch((x-1.2, y-0.6), 2.4, 1.2, boxstyle="round,pad=0.1",
                            facecolor='#81c784', edgecolor=colors['tool'], linewidth=2)
        ax3.add_patch(box)
        ax3.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')
        # Arrow from decision to tool
        ax3.annotate('', xy=(x, y+0.7), xytext=(4.5 if i == 0 else 5.5 if i == 1 else 5.5, 5.4),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Tool results box
    result_box = FancyBboxPatch((3.5, 2.2), 3, 1, boxstyle="round,pad=0.1",
                               facecolor='#66bb6a', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(result_box)
    ax3.text(5, 2.7, 'Tool Results', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows from tools to results
    for x in [1.5, 5, 8.5]:
        ax3.annotate('', xy=(5, 3.3), xytext=(x, 3.3),
                    arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=1.5))
    
    # Final LLM and output
    box_llm2 = FancyBboxPatch((3.5, 0.5), 3, 1, boxstyle="round,pad=0.1",
                             facecolor='#c8e6c9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(box_llm2)
    ax3.text(5, 1, 'LLM\n(Final)', ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax3.annotate('', xy=(5, 1.6), xytext=(5, 2.1),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    
    # Output
    ax3.annotate('', xy=(6.5, 1), xytext=(8, 1),
                arrowprops=dict(arrowstyle='->', color=colors['tool'], lw=2))
    out_box = FancyBboxPatch((8, 0.5), 2, 1, boxstyle="round,pad=0.1",
                            facecolor='#e8f5e9', edgecolor=colors['tool'], linewidth=2)
    ax3.add_patch(out_box)
    ax3.text(9, 1, 'Response:\nCards/PASS', ha='center', va='center', fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/Users/xuborong/Documents/GitHub/ChinesePokerAi/diagrams/architectures_flowchart.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    print("Saved: architectures_flowchart.png")
    plt.close()

if __name__ == "__main__":
    draw_flowchart()
