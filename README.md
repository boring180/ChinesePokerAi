# Chinese Poker AI Research (斗地主 AI 研究)

UROP3200 Research Project: AI Agents Playing Dou Di Zhu (Chinese Poker)

## Project Overview

This project explores different AI approaches for playing Dou Di Zhu (斗地主), a popular Chinese card game. The research compares various AI agent architectures including Chain-of-Thought reasoning, Tool Calling, and Strategy Guide integration.

## Research Features

1. **Chain-of-Thought (CoT) Agents**
   - Step-by-step reasoning before making decisions
   - Analysis of game state, strategy options, and risks

2. **Tool-Calling Agents**
   - Query game history (which cards have been played)
   - Get valid moves and strategic suggestions
   - Search optimal card sequences
   - Win probability estimation

3. **Strategy Guide Integration**
   - RAG-style retrieval from player guides
   - Incorporates beginner, intermediate, and advanced strategies
   - Domain-specific knowledge injection

4. **Full Agents (CoT + Tools + Guide)**
   - Combines all advanced features
   - Most comprehensive AI agent

## Project Structure

```
ChinesePokerAi/
├── game_control.py          # Core game engine (refactored)
├── game_state.py            # Observable game state for AI
├── tools.py                 # Tool calling functions
├── ai_agent.py              # Agent implementations
├── game_runner.py           # Game loop and execution
├── evaluation.py            # Metrics and analysis
├── API_llm.py               # LLM API integration (Qwen)
├── AI_game_play.py          # Main entry point
├── run_experiments.py       # Experiment orchestration
├── guides/                  # Strategy guides
│   ├── beginner_guide.md
│   ├── intermediate_guide.md
│   └── advanced_guide.md
├── experiments/             # Experiment scripts
│   ├── experiment_a.py       # 1 Advanced vs 2 Normal
│   └── experiment_b.py       # 3 Advanced vs 3 Normal
└── results/                 # Experiment outputs
```

## Quick Start

### Prerequisites

```bash
pip install openai  # For Qwen API
```

### Run a Demo Game

```bash
python AI_game_play.py --demo
```

### Run Experiments

**Experiment A: Win Rate Comparison (1 Advanced vs 2 Normal)**
```bash
# Run with CoT agent
python AI_game_play.py --exp-a --agent-type cot --num-games 30

# Run with all agent types
python experiments/experiment_a.py --all --num-games 30
```

**Experiment B: Turn Count Comparison (3 Advanced vs 3 Normal)**
```bash
# Run with Tool agents
python AI_game_play.py --exp-b --agent-type tool --num-games 30

# Run with all agent types
python experiments/experiment_b.py --all --num-games 30
```

**Run Complete Research Suite**
```bash
python AI_game_play.py --all --num-games 30
```

## Experiments

### Experiment A: Win Rate Analysis

**Setup:** 1 Advanced Agent vs 2 Normal Agents
- Player 1: Advanced Agent (CoT/Tool/Full)
- Player 2, 3: Normal Agents (baseline)
- Landlord rotation ensures fairness

**Metrics:**
- Overall win rate
- Win rate as landlord vs farmer
- Error rate
- Turn efficiency

**Research Question:** Do advanced features (CoT, Tools, Guide) improve win rate compared to baseline?

### Experiment B: Efficiency Analysis

**Setup:** Compare turn counts between groups
- Group 1: 3 Advanced Agents
- Group 2: 3 Normal Agents

**Metrics:**
- Average turn count per game (lower = more efficient)
- Standard deviation
- Effect size (Cohen's d)

**Research Question:** Do advanced agents finish games faster (fewer turns)?

## Agent Types

### Normal Agent (Baseline)
- Simple prompt with basic rules
- No advanced reasoning or tools
- Similar to notebook implementation

### CoT Agent (Chain-of-Thought)
- Thinks step-by-step before acting
- Analysis sections: situation, options, risks, decision

### Tool Agent
- Can call tools to get information:
  - `get_valid_moves`: All valid plays
  - `suggest_strategic_move`: Strategy advice
  - `analyze_win_probability`: Win chance
  - `search_optimal_path`: Best card sequence
  - `get_played_cards`: Card history
  - `get_opponent_estimates`: Opponent hand estimate

### Full Agent
- Combines CoT + Tool Calling + Strategy Guide
- Most sophisticated agent
- Best for demonstrating advanced capabilities

## Strategy Guides

Located in `guides/` directory:

1. **Beginner Guide**: Basic rules, common mistakes, fundamental strategy
2. **Intermediate Guide**: Card type analysis, role-specific strategy, probability
3. **Advanced Guide**: Dynamic strategy, opponent modeling, psychological tactics

## Results Format

Experiment results are saved to `results/` directory as JSON files containing:
- Win rates per agent
- Turn counts
- Error rates
- Role-specific performance
- Statistical summaries

## API Configuration

The project uses Alibaba Cloud's DashScope (Qwen) API. Configure your API key in `API_key.json`:

```json
{
    "API_KEY": "your-api-key-here"
}
```

## Code Improvements from Original

1. **Simplified `game_control.py`**: Cleaner class structure, dataclasses, better validation
2. **Separation of Concerns**: Game logic, state tracking, AI agents, and tools are modular
3. **Observable State**: `game_state.py` provides AI-friendly game observation
4. **Tool System**: Extensible tool framework for AI capabilities
5. **Agent Hierarchy**: Base class with specialized implementations
6. **Experiment Framework**: Reproducible experiment configurations
7. **Evaluation Metrics**: Comprehensive statistical analysis

## Usage Examples

```python
# Run a single game
from game_runner import run_single_game
from ai_agent import create_agent

agents = [
    create_agent("cot", "Player1"),
    create_agent("normal", "Player2"),
    create_agent("tool", "Player3"),
]

result = run_single_game(agents, verbose=True)
```

```python
# Run multiple games and evaluate
from evaluation import Evaluator
from ai_agent import CoTAgent, NormalAgent

evaluator = Evaluator()

# Define factories
advanced_factory = lambda name: CoTAgent(name)
normal_factory = lambda name: NormalAgent(name)

# Run Experiment A
result = evaluator.evaluate_experiment_a(
    advanced_agent=CoTAgent("Advanced"),
    normal_agent_factory=normal_factory,
    num_games=30
)
```

## Research Paper Structure (Suggested)

1. **Introduction**: Dou Di Zhu, AI game playing challenges
2. **Related Work**: LLM agents, tool use in games, CoT reasoning
3. **Methodology**: Agent architectures, experimental design
4. **Experiments**: A (win rate) and B (efficiency) results
5. **Analysis**: Performance comparison, feature ablation
6. **Conclusion**: Key findings, limitations, future work

## Citation

If you use this code for your UROP3200 project, please cite:

```
Chinese Poker AI Research (2025)
UROP3200 Project, HKUST
```

## License

This project is for academic research purposes.

## Contact

For questions about this project, please refer to your UROP3200 supervisor.

---

**Happy researching! 🎴🤖**
