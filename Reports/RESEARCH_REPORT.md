This work investigates LLM agent architectures for multi-agent coordination in asymmetric environments. Comparing Baseline, Chain-of-Thought, In-Context Learning, and Tool-Augmented approaches on the card game Fight the Landlord reveals that external tool augmentation significantly outperforms reasoning-based methods. Parallel tool calling enables implicit coordination without explicit communication, informing LLM-based distributed network optimization.

Background
While symbolic AI excel at perfect-information games (Chess, Go), LLM agents' ability to handle multi-agent conversation-based games with asymmetric roles and implicit coordination remains underexplored. Fight the Landlord (Dou Di Zhu) presents unique challenges:
Asymmetric 1v2 structure: One landlord (20 cards) vs two collaborating farmers (17 cards each)
Imperfect information: Hidden hands requiring probabilistic reasoning
Implicit coordination: Farmers must cooperate without communication

Existing benchmarks focus on competitive zero-sum or single-agent tasks. This work addresses cooperative-competitive hybrid environments where agents balance collaboration (farmers) against competition (vs landlord).

Methodology
We compare four LLM prompting strategies on Fight the Landlord (3-player asymmetric card game). Each experiment runs 30 games with rotating roles.

Baseline: Simple rules and game state only.
Chain-of-Thought (CoT): Step-by-step reasoning before decision.
In-Context Learning: Static strategy guides prepended to prompts.
Tool-Augmented: Parallel tool calling for recommendations, best play analysis, valid moves, and game history. Multiple tools execute simultaneously.
Metrics: Win rate (overall and by role), error rate (invalid moves), average turns (game efficiency).















Results
Win Rate Comparison:
Tool-Augmented: 90.0% (27/30) - Best performance
Chain-of-Thought: 80.0% (24/30) - Strong reasoning
In-Context Learning: 56.7% (17/30) - Limited benefit
Baseline: 56.7% (17/30)
Key Findings
Tool-Augmented agents achieve best performance (+33.3% over baseline)
Win rate: 90.0% vs 56.7% baseline (+33.3% improvement)
Perfect landlord performance: 100% (10/10 games)
Lowest error rate: 37.9%
Parallel tool calling enables multi-source reasoning

Chain-of-Thought shows strong results (+23.3% over baseline)
Win rate: 80.0% - second best performance
Strong landlord performance: 90% (9/10 games)
Faster games: 48.7 average turns (most efficient)
Step-by-step reasoning improves decision quality

Tool-Augmented vs CoT comparison
Tool agents: +10% better win rate (90% vs 80%)
Tool agents: Better error handling (37.9% vs 50.9%)
External tools provide reliable information for checking move validity and optimality, while CoT demonstrates that LLM self-reasoning can also produce reasonable decisions.

In-Context Learning remains limited
No improvement over baseline (56.7% vs 56.7% - same performance)
High error rate suggests retrieval overhead
Static guides less effective than dynamic tool queries


















Conclusion
Parallel tool-augmented LLM agents achieve state-of-the-art performance in asymmetric multi-agent card games, reaching a 90% win rate. Parallel tool calling enables agents to synthesize information from multiple sources in a single turn, while structured tool APIs substitute for explicit inter-agent communication.

The 100% landlord win rate demonstrates that LLM agents can master asymmetric competitive roles when equipped with appropriate reasoning tools. These findings inform the design of LLM-based distributed systems where agents coordinate without central control.

However, game logs reveal a limitation: tool-augmented agents may over-rely on external tools rather than developing robust internal reasoning. Since symbolic tools are task-specific, this dependence may limit generalization. Chain-of-Thought reasoning offers a balance—producing transparent, verifiable reasoning while maintaining competitive performance. Future work should investigate hybrid architectures combining tool augmentation with explicit reasoning.

These results extend beyond card games to any multi-agent system requiring coordination under incomplete information, such as distributed robotics, collaborative logistics, and multi-party negotiation.
Future directions:
- Hybrid CoT + tool architectures
- Optimal tool combination analysis
- Larger-scale validation (100+ games)
- Extension to other multi-agent environments

Acknowledgements
The research is supported by Prof. Shenghui SONG in the Department of Integrative Systems and Design, The Hong Kong University of Science and Technology.

Reference
M. Ramesh, K. Jayakumar, A. Ramkumar, P. Thodima, A. Rege, and E.-V. Vlatakis-Gkaragkounis, “Sparks of cooperative reasoning: LLMs as strategic Hanabi agents,” arXiv.org, Jan. 26, 2026. https://arxiv.org/abs/2601.18077
M. Lin et al., “How Far Are LLMs from Professional Poker Players? Revisiting Game-Theoretic Reasoning with Agentic Tool Use,” arXiv.org, Jan. 31, 2026. https://arxiv.org/abs/2602.00528
Y. R. Matinez and J. Roberts, “LLMs as Agentic Cooperative Players in Multiplayer UNO,” arXiv.org, Sep. 11, 2025. https://arxiv.org/abs/2509.09867

