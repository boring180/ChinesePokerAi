"""
AI Agent Implementations for Chinese Poker
Includes: Normal, Chain-of-Thought, Tool-calling, and Full agents
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

from game_control import Player, Series, CardType
from game_state import GameState, CardTracker
from tools import (
    CardHistoryTool, ValidMovesTool, TreeSearchTool,
    execute_tool, get_tool_descriptions, ToolResult
)


@dataclass
class AgentConfig:
    """Configuration for AI agents"""
    use_cot: bool = False  # Chain of Thought
    use_tools: bool = False  # Tool calling
    use_guide: bool = False  # Strategy guide
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_history: int = 20  # Keep last N messages


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(self, name: str, config: AgentConfig):
        self.name = name
        self.config = config
        self.history: List[Dict] = []
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        """Get system prompt for the agent"""
        role = "地主" if is_landlord else "农民"
        return f"你是一个斗地主AI玩家。你是{self.name}，角色是{role}。你的目标是第一个出完所有手牌。"
    
    def build_prompt(self, player: Player, game_state: GameState, 
                     is_retry: bool = False, error_msg: str = "") -> str:
        """Build the prompt for the agent"""
        raise NotImplementedError
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str]]:
        """
        Parse agent response to extract play decision.
        Returns: (is_pass, message, card_strings)
        """
        raise NotImplementedError
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.history.append({"role": role, "content": content})
        # Trim history
        if len(self.history) > self.config.max_history * 2:
            # Keep system messages and recent messages
            system_msgs = [h for h in self.history if h["role"] == "system"]
            recent_msgs = self.history[-self.config.max_history:]
            self.history = system_msgs[:2] + recent_msgs


class NormalAgent(BaseAgent):
    """
    Normal baseline agent - similar to the notebook implementation.
    Uses simple prompt without advanced features.
    """
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig())
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        return f"""你是一个斗地主AI玩家。你是{self.name}，角色是{role}。

规则说明:
1. 目标: 第一个出完所有手牌
2. 牌型: 单牌、对子、三张、三带一、三带二、顺子(5+连续)、连对(3+连续对)、炸弹(四张)、王炸(双王)
3. 大小: 大王>小王>2>A>K>Q>J>10>9>8>7>6>5>4>3
4. 炸弹可以压任何普通牌型，王炸最大
5. 农民需要配合对抗地主

你只需要回答要出的牌，格式如: ♠3♥3♣3
如果不出，回答: PASS 或 不出
不要解释，直接回答牌型。"""
    
    def build_prompt(self, player: Player, game_state: GameState,
                     is_retry: bool = False, error_msg: str = "") -> str:
        # Get basic game info
        hand_str = player.get_cards_string()
        table_str = self._format_table(game_state)
        
        lines = [
            f"你的手牌: {hand_str}",
            f"当前局势: {table_str}",
        ]
        
        # Add opponent info
        for name, remaining, role in game_state.get_opponents_info(player.name):
            lines.append(f"对手 {name} ({role}): 剩{remaining}张牌")
        
        if is_retry:
            lines.append(f"\n注意: 你刚才的出牌有误 - {error_msg}")
            lines.append("请重新选择有效的牌型。")
        
        lines.append("\n请回答你要出的牌 (或回答 PASS):")
        
        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        """Format table state for prompt"""
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌，你是首家可出任意有效牌型"
        return f"桌上: {game_state.table_series} (由{game_state.last_player_name}打出)"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str]]:
        """
        Parse response to extract cards or PASS.
        Returns: (is_pass, message, card_strings)
        """
        response = response.strip().upper()
        
        # Check for PASS
        if response in ["PASS", "不出", "不要", "过", "P"]:
            return True, "PASS", []
        
        # Parse card strings
        # Format: ♠3♥3♣3 or ♠3 ♥3 ♣3
        import re
        
        # Extract card patterns
        # Support: ♠3, ♥10, 小王, 大王, etc.
        cards = []
        
        # Pattern for suited cards
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA]|[3-9])'
        suited_matches = re.findall(suited_pattern, response)
        cards.extend(suited_matches)
        
        # Pattern for jokers
        if '小王' in response:
            cards.append('小王')
        if '大王' in response:
            cards.append('大王')
        
        # Also try space-separated format
        if not cards:
            parts = response.replace(',', ' ').split()
            cards = [p for p in parts if p]
        
        return False, response, cards


class CoTAgent(BaseAgent):
    """
    Chain-of-Thought Agent.
    Thinks step-by-step before making a decision.
    """
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig(use_cot=True))
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        return f"""你是一个使用思维链(CoT)的斗地主AI玩家。你是{self.name}，角色是{role}。

你需要先思考分析，然后给出最终决定。

思考步骤:
1. 【局势分析】分析当前牌局，包括你的手牌、桌上的牌、对手剩余牌数
2. 【可选策略】列出你可以出的有效牌型，或选择PASS
3. 【风险评估】评估每种选择的利弊
4. 【最终决定】选择最优策略并给出牌型

输出格式:
思考: <你的分析过程>
回答: <最终要出的牌，如 ♠3♥3♣3 或 PASS>"""
    
    def build_prompt(self, player: Player, game_state: GameState,
                     is_retry: bool = False, error_msg: str = "") -> str:
        hand_str = player.get_cards_string()
        table_str = self._format_table(game_state)
        
        lines = [
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
            f"当前局势: {table_str}",
            "",
            "对手状态:",
        ]
        
        for name, remaining, role in game_state.get_opponents_info(player.name):
            lines.append(f"  - {name} ({role}): {remaining}张牌")
        
        if is_retry:
            lines.append(f"\n⚠️ 修正: 你刚才的出牌有误 - {error_msg}")
        
        lines.append("\n请按格式输出你的思考和回答:")
        
        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌，你是首家"
        return f"桌上有 {game_state.table_series}"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str]]:
        """Parse CoT response to extract final decision"""
        # Extract the "回答" part
        lines = response.strip().split('\n')
        
        # Look for "回答:" or "回答：" or "Answer:" or similar
        answer_line = None
        for line in lines:
            line_lower = line.lower()
            if any(marker in line_lower for marker in ['回答:', '回答：', 'answer:', 'answer：', '最终决定:', '出牌:']):
                answer_line = line
                break
        
        # If no marker found, use last non-empty line
        if answer_line is None:
            for line in reversed(lines):
                stripped = line.strip()
                if stripped and '思考' not in stripped:
                    answer_line = stripped
                    break
        
        if answer_line is None:
            answer_line = response
        
        # Extract just the card part after the marker
        for marker in ['回答:', '回答：', 'answer:', 'answer：', '最终决定:', '出牌:', '出牌：']:
            if marker in answer_line:
                answer_line = answer_line.split(marker, 1)[-1].strip()
                break
        
        # Now parse the answer line as cards
        answer_line = answer_line.strip()
        
        # Check for PASS
        if answer_line.upper() in ["PASS", "不出", "不要", "过", "P", ""]:
            return True, response, []
        
        # Parse cards
        import re
        cards = []
        
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA]|[3-9])'
        suited_matches = re.findall(suited_pattern, answer_line)
        cards.extend(suited_matches)
        
        if '小王' in answer_line:
            cards.append('小王')
        if '大王' in answer_line:
            cards.append('大王')
        
        return False, response, cards


class ToolAgent(BaseAgent):
    """
    Tool-Calling Agent.
    Can use tools to query game state and analyze options.
    """
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig(use_tools=True))
        self.tools_used_this_turn = []
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        tools_desc = get_tool_descriptions()
        
        return f"""你是一个使用工具的斗地主AI玩家。你是{self.name}，角色是{role}。

你可以使用以下工具来辅助决策:
{tools_desc}

使用方法:
1. 工具调用: 输入 "TOOL:工具名" 调用工具
2. 你可以调用多个工具获取信息
3. 基于工具结果，给出你的出牌决策

输出格式:
工具: <调用的工具名>
思考: <基于工具结果的分析>
回答: <最终要出的牌，如 ♠3♥3♣3 或 PASS>"""
    
    def build_prompt(self, player: Player, game_state: GameState,
                     card_tracker: Optional[CardTracker] = None,
                     is_retry: bool = False, error_msg: str = "") -> str:
        hand_str = player.get_cards_string()
        
        lines = [
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
            f"当前局势: {self._format_table(game_state)}",
            "",
            "可用工具:",
            "  - get_valid_moves: 获取所有有效出牌",
            "  - suggest_strategic_move: 获取策略建议",
            "  - analyze_win_probability: 评估胜率",
            "  - get_opponent_estimates: 估算对手手牌",
            "  - search_optimal_path: 搜索最优出牌序列",
        ]
        
        if is_retry:
            lines.append(f"\n⚠️ 修正: 你刚才的出牌有误 - {error_msg}")
        
        lines.append("\n你可以先调用工具获取信息，然后做出决策。")
        lines.append("格式: 工具:工具名 或 直接回答: 牌型")
        
        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌，你是首家"
        return f"桌上有 {game_state.table_series} (需压过此牌)"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], bool]:
        """
        Parse tool agent response.
        Returns: (is_pass, full_response, card_strings, is_tool_call)
        """
        response = response.strip()
        
        # Check if it's a tool call
        if response.upper().startswith("TOOL:") or response.startswith("工具:"):
            tool_name = response.split(":", 1)[-1].strip()
            return False, response, [tool_name], True
        
        # Regular card parsing
        is_pass, _, cards = NormalAgent("").parse_response(response)
        return is_pass, response, cards, False
    
    def execute_tool_call(self, tool_name: str, player: Player, 
                         game_state: GameState, card_tracker: CardTracker) -> str:
        """Execute a tool call and return result"""
        self.tools_used_this_turn.append(tool_name)
        
        # Map tool names
        tool_mapping = {
            "get_valid_moves": lambda: ValidMovesTool.get_valid_moves(
                player, game_state.table_series
            ),
            "suggest_strategic_move": lambda: ValidMovesTool.suggest_strategic_move(
                player, game_state
            ),
            "analyze_win_probability": lambda: TreeSearchTool.analyze_win_probability(
                player, game_state
            ),
            "get_opponent_estimates": lambda: self._get_opponent_estimate(
                game_state, player.name
            ),
            "search_optimal_path": lambda: TreeSearchTool.search_optimal_path(
                player.cards, max_depth=5
            ),
            "get_played_cards": lambda: CardHistoryTool.get_played_cards(
                game_state
            ),
            "get_high_cards_remaining": lambda: CardHistoryTool.get_high_cards_remaining(
                game_state, card_tracker
            ),
        }
        
        if tool_name not in tool_mapping:
            return f"未知工具: {tool_name}"
        
        try:
            result: ToolResult = tool_mapping[tool_name]()
            return f"【{tool_name} 结果】\n{result.result}"
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    def _get_opponent_estimate(self, game_state: GameState, player_name: str) -> ToolResult:
        """Get estimate for first opponent"""
        opponents = [p for p in game_state.players if p.name != player_name]
        if not opponents:
            return ToolResult("get_opponent_estimates", "无对手信息", {})
        return CardHistoryTool.get_opponent_estimates(game_state, opponents[0].name)
    
    def reset_tools(self):
        """Reset tools used counter"""
        self.tools_used_this_turn = []


class FullAgent(CoTAgent, ToolAgent):
    """
    Full Agent combining Chain-of-Thought + Tool Calling + Guide Reading.
    Most advanced agent type.
    """
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None,
                 guide_content: Optional[str] = None):
        super().__init__(name, config or AgentConfig(
            use_cot=True, 
            use_tools=True, 
            use_guide=True
        ))
        self.guide_content = guide_content or ""
        self.tools_used_this_turn = []
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        
        base_prompt = f"""你是一个高级的斗地主AI玩家。你是{self.name}，角色是{role}。

你具备以下高级能力:
1. 【思维链(CoT)】逐步分析局势后再决策
2. 【工具调用】使用工具获取深度信息
3. 【策略指南】参考专业策略知识

工作流程:
1. 局势观察 - 了解当前牌局状态
2. 工具调用 - 使用工具获取有效出牌、胜率评估等信息
3. 策略分析 - 结合策略指南思考最优解
4. 决策输出 - 给出最终出牌

输出格式:
观察: <当前局势>
工具: <使用的工具及结果>
分析: <基于工具结果和策略的分析>
回答: <最终要出的牌，如 ♠3♥3♣3 或 PASS>"""
        
        if self.guide_content:
            base_prompt += f"\n\n【策略指南参考】\n{self.guide_content[:1500]}..."
        
        return base_prompt
    
    def build_prompt(self, player: Player, game_state: GameState,
                     card_tracker: Optional[CardTracker] = None,
                     is_retry: bool = False, error_msg: str = "") -> str:
        hand_str = player.get_cards_string()
        
        # Get game progress
        progress = game_state.get_game_progress_summary()
        
        lines = [
            "=" * 40,
            f"【回合 {game_state.turn_count}】{self.name}的决策",
            "=" * 40,
            "",
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
            "",
            progress,
            "",
            "可用工具:",
            "  TOOL:get_valid_moves - 获取所有有效出牌选项",
            "  TOOL:suggest_strategic_move - 获取策略建议",
            "  TOOL:analyze_win_probability - 评估胜率",
            "  TOOL:search_optimal_path - 搜索最优出牌序列",
            "  TOOL:get_opponent_estimates - 估算对手手牌",
            "",
        ]
        
        if is_retry:
            lines.append(f"⚠️ 修正: 你刚才的出牌有误 - {error_msg}")
            lines.append("请重新分析并给出正确答案。\n")
        
        lines.append("请按格式输出你的完整思考过程:")
        
        return "\n".join(lines)
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], bool]:
        """
        Parse full agent response.
        Returns: (is_pass, full_response, card_strings, is_tool_call)
        """
        response = response.strip()
        
        # Check for tool call first
        for marker in ["TOOL:", "工具:", "tool:", "调用:", "调用工具:"]:
            if marker in response:
                # Extract tool name
                lines = response.split('\n')
                for line in lines:
                    if marker in line:
                        parts = line.split(marker, 1)[-1].strip()
                        tool_name = parts.split()[0].strip(':')
                        return False, response, [tool_name], True
        
        # Look for final answer
        lines = response.split('\n')
        answer_line = None
        
        for line in lines:
            line_stripped = line.strip()
            for marker in ['回答:', '回答：', 'answer:', 'answer：', '出牌:', '出牌：', '最终决定:']:
                if marker in line_stripped.lower():
                    answer_line = line_stripped.split(marker, 1)[-1].strip()
                    break
        
        if answer_line is None:
            # Use last line as fallback
            for line in reversed(lines):
                stripped = line.strip()
                if stripped and not any(x in stripped.lower() for x in ['观察:', '工具:', '分析:', '思考:']):
                    answer_line = stripped
                    break
        
        if answer_line is None:
            answer_line = response
        
        # Parse cards from answer
        import re
        cards = []
        
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA]|[3-9])'
        suited_matches = re.findall(suited_pattern, answer_line)
        cards.extend(suited_matches)
        
        if '小王' in answer_line:
            cards.append('小王')
        if '大王' in answer_line:
            cards.append('大王')
        
        # Check for PASS
        is_pass = answer_line.upper() in ["PASS", "不出", "不要", "过", "P", ""] or not cards
        
        return is_pass, response, cards, False


def create_agent(agent_type: str, name: str, **kwargs) -> BaseAgent:
    """
    Factory function to create agents by type.
    
    Args:
        agent_type: "normal", "cot", "tool", or "full"
        name: Agent name
        **kwargs: Additional configuration
    
    Returns:
        BaseAgent instance
    """
    agent_map = {
        "normal": NormalAgent,
        "cot": CoTAgent,
        "tool": ToolAgent,
        "full": FullAgent,
    }
    
    if agent_type not in agent_map:
        raise ValueError(f"Unknown agent type: {agent_type}. Use: {list(agent_map.keys())}")
    
    return agent_map[agent_type](name, **kwargs)


def load_strategy_guide(guide_path: str) -> str:
    """Load strategy guide from file"""
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[无法加载策略指南: {str(e)}]"
