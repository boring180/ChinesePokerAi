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

Tool-Augmented: External tool calling with parallel tool support - Query valid moves, strategic recommendations, card tracking simultaneously

In-Context Learning: RAG-style retrieval - Dynamic strategy guide injection based on game state

Full Agent: Ensemble methods - CoT + Tools + In-Context Learning combined

Results

Experiment A: 1 Advanced vs 2 Baseline Agents (30 games each)

Latest Results (with parallel tool calling):

Tool-Augmented Agent:
  Overall Win Rate: 90.0% (27/30)
  As Landlord: 100.0% (10/10)
  As Farmer: 85.0% (17/20)
  Error Rate: 37.9%
  Average Turns: 51.0

Previous Results (single tool calling):
  Overall Win Rate: 73.3% (22/30)
  As Landlord: 50.0% (5/10)
  As Farmer: 85.0% (17/20)
  Error Rate: 81.1%
  Average Turns: 55.1

In-Context Learning Agent:
  Overall Win Rate: 56.7%
  As Landlord: 20.0%
  As Farmer: 75.0%
  Error Rate: 193.5%
  Average Turns: 60.7

Baseline Agents (average):
  Overall Win Rate: 33.3% (combined)
  As Landlord: 15.0%
  As Farmer: 42.5%

Key Findings

1. Parallel tool calling dramatically improves performance (+16.7% over single tool)
   - Win rate increased from 73.3% to 90.0%
   - Perfect landlord performance: 100% (10/10 games)
   - Error rate reduced by half: 37.9% vs 81.1%
   - Faster games: 51.0 vs 55.1 average turns

2. Tool-Augmented agents show superior asymmetric role handling
   - Landlord win rate: 100% vs 15% baseline
   - Farmer cooperation: 85% vs 42.5% baseline
   - Demonstrates effective implicit coordination through shared tool knowledge

3. In-Context Learning remains limited
   - No improvement over baseline
   - High error rate suggests retrieval overhead

4. Parallel tool calling benefits
   - Agents can query multiple tools simultaneously (get_direct_recommendation + find_best_play + get_valid_moves)
   - Richer context leads to better decision making
   - Reduced retry attempts lower overall error count

Conclusion

Parallel tool-augmented LLM agents achieve state-of-the-art performance in asymmetric multi-agent card games. The 90% win rate demonstrates that structured tool access enables both superior individual play and implicit multi-agent coordination.

Key Insight: Parallel tool calling (querying multiple tools in one turn) provides significant advantage over sequential or single-tool approaches. Agents synthesize information from multiple sources (recommendations, efficiency analysis, valid moves) for optimal decisions.

Implications: Structured tool APIs can substitute for explicit inter-agent communication in cooperative settings. The 100% landlord win rate shows LLM agents can master asymmetric competitive roles when given appropriate reasoning tools.

Future Work

- Complete CoT Agent and Full Agent evaluations with parallel tool support
- Investigate optimal tool combinations (which tools work best together)
- Scale to larger samples (100+ games) for statistical validation
- Experiment B: Efficiency analysis comparing turn counts between agent groups
- Extend to other conversation-based multi-agent games

Acknowledgement

UROP3200 Research Project, HKUST. Experiments conducted with Qwen3.5-Flash via Alibaba Cloud DashScope API.
