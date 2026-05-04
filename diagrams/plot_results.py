import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Set style for academic paper
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

# Data
agents = ['Tool-\nAugmented', 'Chain-of-\nThought', 'In-Context\nLearning', 'Baseline']
win_rates = [90.0, 80.0, 56.7, 33.3]
error_rates = [37.9, 50.9, 193.5, 193.5]

# Colors - academic color palette
colors = ['#2E7D32', '#689F38', '#F9A825', '#C62828']

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Win Rate
bars1 = ax1.bar(agents, win_rates, color=colors, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Win Rate (%)', fontweight='bold')
ax1.set_title('Agent Performance: Win Rate\n(30 games, 1 Advanced vs 2 Baseline)', fontweight='bold', pad=15)
ax1.set_ylim(0, 100)
ax1.axhline(y=33.3, color='gray', linestyle='--', alpha=0.5, label='Baseline average')

# Add value labels on bars
for bar, val in zip(bars1, win_rates):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Plot 2: Error Rate
bars2 = ax2.bar(agents, error_rates, color=colors, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Error Rate (%)', fontweight='bold')
ax2.set_title('Agent Performance: Error Rate\n(Lower is Better)', fontweight='bold', pad=15)
ax2.set_ylim(0, 220)

# Add value labels on bars
for bar, val in zip(bars2, error_rates):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
             f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)

ax2.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('results_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('results_comparison.pdf', bbox_inches='tight', facecolor='white')
print("Saved: results_comparison.png and results_comparison.pdf")

# Create detailed comparison chart
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(agents))
width = 0.35

# Grouped bar chart
bars1 = ax.bar(x - width/2, win_rates, width, label='Win Rate (%)', 
               color='#2E7D32', edgecolor='black', linewidth=1.2)
bars2 = ax.bar(x + width/2, [e/2 for e in error_rates], width, label='Error Rate/2 (%)', 
               color='#C62828', edgecolor='black', linewidth=1.2, alpha=0.7)

ax.set_ylabel('Percentage (%)', fontweight='bold')
ax.set_title('Agent Architecture Comparison: Win Rate vs Error Rate\n(Experiment A: 30 Games)', 
             fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(agents)
ax.legend(loc='upper right', framealpha=0.9)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add annotations
for i, (w, e) in enumerate(zip(win_rates, error_rates)):
    ax.annotate(f'{w:.1f}%', xy=(i - width/2, w), xytext=(0, 3),
                textcoords="offset points", ha='center', va='bottom',
                fontweight='bold', fontsize=10)
    ax.annotate(f'{e:.1f}%', xy=(i + width/2, e/2), xytext=(0, 3),
                textcoords="offset points", ha='center', va='bottom',
                fontweight='bold', fontsize=9, color='#C62828')

plt.tight_layout()
plt.savefig('results_detailed.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('results_detailed.pdf', bbox_inches='tight', facecolor='white')
print("Saved: results_detailed.png and results_detailed.pdf")

# Create role-specific performance chart
fig, ax = plt.subplots(figsize=(10, 6))

roles = ['Landlord', 'Farmer']
tool_role = [100.0, 85.0]
cot_role = [90.0, 75.0]
icl_role = [20.0, 75.0]
baseline_role = [15.0, 42.5]

x = np.arange(len(roles))
width = 0.2

ax.bar(x - 1.5*width, tool_role, width, label='Tool-Augmented', color='#2E7D32', edgecolor='black')
ax.bar(x - 0.5*width, cot_role, width, label='Chain-of-Thought', color='#689F38', edgecolor='black')
ax.bar(x + 0.5*width, icl_role, width, label='In-Context Learning', color='#F9A825', edgecolor='black')
ax.bar(x + 1.5*width, baseline_role, width, label='Baseline', color='#C62828', edgecolor='black')

ax.set_ylabel('Win Rate (%)', fontweight='bold')
ax.set_title('Role-Specific Performance: Landlord vs Farmer Win Rates', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(roles)
ax.legend(loc='upper right', framealpha=0.9)
ax.set_ylim(0, 110)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('results_by_role.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('results_by_role.pdf', bbox_inches='tight', facecolor='white')
print("Saved: results_by_role.png and results_by_role.pdf")

plt.close('all')
