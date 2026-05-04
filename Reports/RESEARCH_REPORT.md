Evaluating LLM Agent Architectures for Multi-Agent Collaboration in Asymmetric Card Games

Abstract

This work investigates LLM agent architectures for multi-agent coordination in asymmetric environments. Comparing Baseline, Chain-of-Thought, In-Context Learning, and Tool-Augmented approaches on Fight the Landlord reveals that external tool augmentation significantly outperforms reasoning-based methods. Parallel tool calling enables implicit coordination without explicit communication, informing LLM-based distributed network optimization.

Background

Research Gap

While RL agents excel at perfect-information games (Chess, Go), LLM agents' ability to handle multi-agent conversation-based games with asymmetric roles and implicit coordination remains underexplored. Fight the Landlord (Dou Di Zhu) presents unique challenges:

1. Asymmetric 1v2 structure: One landlord (20 cards) vs two collaborating farmers (17 cards each)
2. Imperfect information: Hidden hands requiring probabilistic reasoning
3. Implicit coordination: Farmers must cooperate without communication

Existing benchmarks focus on competitive zero-sum or single-agent tasks. This work addresses cooperative-competitive hybrid environments where agents balance collaboration (farmers) against competition (vs landlord).

Methodology

Experimental Setup

We compare four LLM prompting strategies on Fight the Landlord (3-player asymmetric card game). Each experiment runs 30 games with rotating roles.

Baseline: Simple rules and game state only.
Chain-of-Thought (CoT): Step-by-step reasoning before decision.
In-Context Learning: Static strategy guides prepended to prompts.
Tool-Augmented: Parallel tool calling for recommendations, best play analysis, valid moves, and game history. Multiple tools execute simultaneously.

Metrics: Win rate (overall and by role), error rate (invalid moves), average turns (game efficiency).

Results

Win Rate Comparison:
  Tool-Augmented:     90.0% (27/30) - Best performance
  Chain-of-Thought:   80.0% (24/30) - Strong reasoning
  In-Context Learning: 56.7% (17/30) - Limited benefit
  Baseline (avg):     33.3% (10/30) - Control condition

Detailed Metrics:

Tool-Augmented Agent:
  Overall Win Rate: 90.0%
  As Landlord: 100.0% (10/10)
  As Farmer: 85.0% (17/20)
  Error Rate: 37.9%
  Average Turns: 51.0

Chain-of-Thought Agent:
  Overall Win Rate: 80.0%
  As Landlord: 90.0% (9/10)
  As Farmer: 75.0% (15/20)
  Error Rate: 50.9%
  Average Turns: 48.7

In-Context Learning Agent:
  Overall Win Rate: 56.7%
  As Landlord: 20.0%
  As Farmer: 75.0%
  Error Rate: 193.5%
  Average Turns: 60.7

Baseline Agents (average):
  Overall Win Rate: 33.3%
  As Landlord: 15.0%
  As Farmer: 42.5%

Key Findings

1. Tool-Augmented agents achieve best performance (+56.7% over baseline)
   - Win rate: 90.0% vs 33.3% baseline
   - Perfect landlord performance: 100% (10/10 games)
   - Lowest error rate: 37.9%
   - Parallel tool calling enables multi-source reasoning

2. Chain-of-Thought shows strong results (+46.7% over baseline)
   - Win rate: 80.0% - second best performance
   - Strong landlord performance: 90% (9/10 games)
   - Faster games: 48.7 average turns (most efficient)
   - Step-by-step reasoning improves decision quality

3. Tool-Augmented vs CoT comparison
   - Tool agents: +10% better win rate (90% vs 80%)
   - Tool agents: Better error handling (37.9% vs 50.9%)
   - External tools provide reliable information for checking move validity and optimality, while CoT demonstrates that LLM self-reasoning can also produce reasonable decisions.

4. In-Context Learning remains limited
   - No improvement over baseline (56.7% vs 33.3% for normal agents)
   - High error rate suggests retrieval overhead
   - Static guides less effective than dynamic tool queries

Conclusion

Parallel tool-augmented LLM agents achieve state-of-the-art performance in asymmetric multi-agent card games. The 90% win rate demonstrates that structured tool access enables both superior individual play and implicit multi-agent coordination.

Key Insight: Parallel tool calling enables agents to synthesize information from multiple sources (recommendations, efficiency analysis, valid moves) in a single turn for optimal decision making.

Implications: Structured tool APIs can substitute for explicit inter-agent communication in cooperative settings. The 100% landlord win rate shows LLM agents can master asymmetric competitive roles when given appropriate reasoning tools.

Future Work

- Complete CoT Agent evaluation with parallel tool support
- Investigate optimal tool combinations (which tools work best together)
- Scale to larger samples (100+ games) for statistical validation
- Experiment B: Efficiency analysis comparing turn counts between agent groups
- Extend to other conversation-based multi-agent games

Acknowledgement

The research is supported by Prof. Shenghui SONG in the Department of Integrative Systems and Design, The Hong Kong University of Science and Technology.

https://arxiv.org/abs/2601.18077
https://arxiv.org/abs/2602.00528
https://arxiv.org/abs/2509.09867