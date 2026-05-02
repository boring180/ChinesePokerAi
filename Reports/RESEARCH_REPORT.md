Evaluating LLM Agent Architectures for Multi-Agent Collaboration in Asymmetric Card Games

Background

Research Gap

While RL agents excel at perfect-information games (Chess, Go), LLM agents' ability to handle multi-agent conversation-based games with asymmetric roles and implicit coordination remains underexplored. Fight the Landlord (Dou Di Zhu) presents unique challenges:

1. Asymmetric 1v2 structure: One landlord (20 cards) vs two collaborating farmers (17 cards each)
2. Imperfect information: Hidden hands requiring probabilistic reasoning
3. Implicit coordination: Farmers must cooperate without communication

Existing benchmarks focus on competitive zero-sum or single-agent tasks. This work addresses cooperative-competitive hybrid environments where agents balance collaboration (farmers) against competition (vs landlord).

Agent Architectures

Baseline: Zero-shot prompting with simple rules (control condition)

Chain-of-Thought (CoT): Step-by-step reasoning - Situation analysis → options evaluation → risks assessment → decision

Tool-Augmented: External tool calling - Query valid moves, strategic recommendations from symbolic reasoning, deck reading

In-Context Learning: Dynamic strategy guide injection based on game state

Results
Tool-Augmented Agent:
  Overall Win Rate: 73.3%
  As Landlord: 50.0%
  As Farmer: 85.0%
  Error Rate: 81.1%

In-Context Learning Agent:
  Overall Win Rate: 56.7%
  As Landlord: 20.0%
  As Farmer: 75.0%
  Error Rate: 193.5%

Baseline Agents (average):
  Overall Win Rate: 55.0%
  As Landlord: 15.0%
  As Farmer: 72.5%

Key Findings

1. Tool-Augmentation improves coordination by +18.3% win rate over baseline. Farmer cooperation achieves 85.0% vs 72.5% for baseline farmers.

2. In-Context Learning shows limited benefit. Win rate comparable to baseline (56.7% vs 55.0%) but higher error rate suggests retrieval overhead may distract from gameplay.

3. Erroe were introduced when the agent produce invalid moves. Structured tool queries significantly reduce errors (81.1% vs 193.5% error rate).

Conclusion

Tool-Augmented agents excel at implicit multi-agent coordination. External tools substitute for explicit inter-agent communication by providing shared structured knowledge. This suggests a promising direction for AI collaboration: structured APIs enable coordination without message-passing overhead.

Chain-of-Thought reasoning alone is insufficient for imperfect-information games. Reasoning without validation generates plausible but invalid moves at high rates.

Future Work

- Complete CoT Agent and Full Agent evaluations
- Compare inter-agent communication vs implicit coordination
- Scale to larger samples for statistical significance testing

Acknowledgement

UROP3200 Research Project, HKUST. Experiments conducted with Qwen3.5-Flash via Alibaba Cloud DashScope API.
