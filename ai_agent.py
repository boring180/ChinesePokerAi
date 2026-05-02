"""
AI Agent Implementations for Chinese Poker
True Tool-Calling Agent Design
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

from game_control import Player, Series, CardType
from game_state import GameState, CardTracker


@dataclass
class AgentConfig:
    """Configuration for AI agents"""
    use_cot: bool = False  # Chain of Thought
    use_tools: bool = False  # Tool calling
    use_guide: bool = False  # Strategy guide
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_history: int = 20


class ToolCall:
    """Represents a tool call from the agent"""
    def __init__(self, tool_name: str, tool_input: str = ""):
        self.tool_name = tool_name.strip().lower().replace(" ", "_")
        self.tool_input = tool_input.strip()
    
    def __repr__(self):
        return f"ToolCall({self.tool_name})"


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(self, name: str, config: AgentConfig):
        self.name = name
        self.config = config
        self.history: List[Dict] = []
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        """Get system prompt for the agent"""
        raise NotImplementedError
    
    def build_prompt(self, player: Player, game_state: GameState, **kwargs) -> str:
        """Build the prompt for the agent"""
        raise NotImplementedError
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        """
        Parse agent response.
        Returns: (is_pass, full_response, card_strings, tool_call)
        - If tool_call is not None, the agent wants to call a tool
        - If is_pass is True, the agent passes
        - Otherwise, card_strings contains the cards to play
        """
        raise NotImplementedError
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.config.max_history * 2:
            system_msgs = [h for h in self.history if h.get("role") == "system"]
            recent_msgs = self.history[-self.config.max_history:]
            self.history = system_msgs[:2] + recent_msgs

    def _format_game_history(self, game_state: GameState, player_name: str, max_plays: int = 10) -> str:
        """Format recent game history for the prompt"""
        if not game_state.play_history:
            return ""

        lines = ["【最近出牌记录】"]

        # Get recent plays (excluding current player's own plays)
        recent_plays = []
        for record in reversed(game_state.play_history):
            if len(recent_plays) >= max_plays:
                break
            if record.player_name != player_name:
                recent_plays.append(record)

        if not recent_plays:
            return ""

        # Reverse to show chronological order
        recent_plays.reverse()

        for record in recent_plays:
            if record.is_pass:
                lines.append(f"  {record.player_name}: PASS")
            else:
                lines.append(f"  {record.player_name}: {record.series}")

        return "\n".join(lines)


class NormalAgent(BaseAgent):
    """Normal baseline agent - simple prompt without advanced features"""
    
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
如果不出，回答: PASS
不要解释，直接回答牌型。"""
    
    def build_prompt(self, player: Player, game_state: GameState, **kwargs) -> str:
        hand_str = player.get_cards_string()
        table_str = self._format_table(game_state)

        lines = [
            f"你的手牌: {hand_str}",
            f"当前局势: {table_str}",
        ]

        for name, remaining, role in game_state.get_opponents_info(player.name):
            lines.append(f"对手 {name} ({role}): 剩{remaining}张牌")

        # Add game history
        history_str = self._format_game_history(game_state, player.name)
        if history_str:
            lines.append("")
            lines.append(history_str)

        if kwargs.get('is_retry'):
            lines.append("")
            lines.append(f"⚠️ 出牌错误: {kwargs.get('error_msg', '')}")

        lines.append("")
        lines.append("请回答你要出的牌 (或回答 PASS):")
        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌，你是首家可出任意有效牌型"
        return f"桌上: {game_state.table_series} (由{game_state.last_player_name}打出)"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        original_response = response.strip()
        response_upper = original_response.upper()
        
        # Check for PASS
        if response_upper in ["PASS", "不出", "不要", "过", "P", ""]:
            return True, original_response, [], None
        
        # Parse card strings
        cards = []
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA])'
        suited_matches = re.findall(suited_pattern, original_response)
        cards.extend(suited_matches)
        
        if '小王' in original_response:
            cards.append('小王')
        if '大王' in original_response:
            cards.append('大王')
        
        return False, original_response, cards, None


class CoTAgent(BaseAgent):
    """Chain-of-Thought Agent"""
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig(use_cot=True))
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        return f"""你是一个使用思维链(CoT)的斗地主AI玩家。你是{self.name}，角色是{role}。

你需要先思考分析，然后给出最终决定。

思考步骤:
1. 【局势分析】分析当前牌局
2. 【可选策略】列出你可以出的有效牌型
3. 【风险评估】评估每种选择的利弊
4. 【最终决定】选择最优策略并给出牌型

输出格式:
思考: <你的分析>
回答: <牌型，如 ♠3♥3♣3 或 PASS>"""
    
    def build_prompt(self, player: Player, game_state: GameState, **kwargs) -> str:
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

        # Add game history
        history_str = self._format_game_history(game_state, player.name)
        if history_str:
            lines.append("")
            lines.append(history_str)

        if kwargs.get('is_retry'):
            lines.append("")
            lines.append(f"⚠️ 出牌错误: {kwargs.get('error_msg', '')}")

        lines.append("")
        lines.append("请按格式输出你的思考和回答:")
        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌"
        return f"桌上有 {game_state.table_series}"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        # Extract the "回答" part
        lines = response.strip().split('\n')
        answer_line = None
        
        for line in lines:
            line_lower = line.lower()
            if any(marker in line_lower for marker in ['回答:', '回答：', 'answer:', '出牌:', '最终决定:']):
                answer_line = line
                break
        
        if answer_line is None:
            for line in reversed(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('思考'):
                    answer_line = stripped
                    break
        
        if answer_line is None:
            answer_line = response
        
        # Extract just the card part
        for marker in ['回答:', '回答：', 'answer:', 'answer：', '最终决定:', '出牌:', '出牌：']:
            if marker in answer_line.lower():
                answer_line = answer_line.split(marker, 1)[-1].strip()
                break
        
        # Check for PASS
        if answer_line.upper() in ["PASS", "不出", "不要", "过", "P", ""]:
            return True, response, [], None
        
        # Parse cards
        cards = []
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA])'
        suited_matches = re.findall(suited_pattern, answer_line)
        cards.extend(suited_matches)
        
        if '小王' in answer_line:
            cards.append('小王')
        if '大王' in answer_line:
            cards.append('大王')
        
        return False, response, cards, None


class GuideAgent(BaseAgent):
    """Guide-Reading Agent"""
    
    def __init__(self, name: str, guide_content: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig(use_guide=True))
        self.guide_content = guide_content
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        return f"""你是一个斗地主AI玩家。你是{self.name}，角色是{role}。

你的特点：直接根据策略指南出牌，不思考分析。

规则：
1. 阅读策略指南
2. 直接给出要出的牌
3. 不要解释，不要分析

输出格式:
回答: <牌型，如 ♠3♥3♣3 或 PASS>"""
    
    def build_prompt(self, player: Player, game_state: GameState, **kwargs) -> str:
        hand_str = player.get_cards_string()

        lines = [
            "【策略指南参考】",
            self.guide_content[:1000],
            "",
            "=" * 40,
            "",
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
        ]

        if game_state.table_series.type == CardType.INVALID:
            lines.append("桌上无牌，你是首家可出任意有效牌型")
        else:
            lines.append(f"桌上: {game_state.table_series}")

        for name, remaining, role in game_state.get_opponents_info(player.name):
            lines.append(f"对手 {name} ({role}): 剩{remaining}张牌")

        # Add game history
        history_str = self._format_game_history(game_state, player.name)
        if history_str:
            lines.append("")
            lines.append(history_str)

        if kwargs.get('is_retry'):
            lines.append("")
            lines.append(f"⚠️ 出牌错误: {kwargs.get('error_msg', '')}")

        lines.append("")
        lines.append("直接给出你要出的牌（不要思考分析）:")
        return "\n".join(lines)

    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        """Parse response - Guide agent doesn't think, just plays"""
        original_response = response.strip()
        response_upper = original_response.upper()

        # Check for PASS
        if response_upper in ["PASS", "不出", "不要", "过", "P", ""]:
            return True, original_response, [], None

        # Parse card strings directly (no thinking section)
        cards = []
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA])'
        suited_matches = re.findall(suited_pattern, original_response)
        cards.extend(suited_matches)

        if '小王' in original_response:
            cards.append('小王')
        if '大王' in original_response:
            cards.append('大王')

        return False, original_response, cards, None


class ToolAgent(BaseAgent):
    """
    True Tool-Calling Agent.
    
    FLOW:
    1. Agent sees prompt with available tools
    2. Agent can either:
       - Call ONE tool (format: TOOL: tool_name)
       - Play cards directly (format: 回答: ♠3♣3)
    3. If tool called: Execute tool, return result
    4. Agent sees tool result, must play cards (no more tools)
    
    After tool result is shown, the agent CANNOT call another tool.
    """
    
    AVAILABLE_TOOLS = {
        "get_direct_recommendation": "AI直接推荐最优出牌（最优先使用）",
        "find_best_play": "搜索最优出牌（最大化弃牌数量）",
        "get_valid_moves": "列出所有合法出牌选项",
        "get_played_cards": "查询已出牌历史",
        "get_remaining_deck": "查询剩余牌分布",
    }
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        super().__init__(name, config or AgentConfig(use_tools=True))
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        tools_list = "\n".join([f"  - {name}: {desc}" for name, desc in self.AVAILABLE_TOOLS.items()])

        if is_landlord:
            role_strategy = """【地主核心策略 - 必须遵守】
你是1v2，必须主动进攻:
1. 首家出牌时 → 优先出顺子、连对，快速减少手牌数量
2. 农民压过你时 → 能压回来就压，保持出牌权
3. 农民剩牌≤3张时 → 必须压制，有炸弹用炸弹
4. 永远不要浪费炸弹！炸弹是最后手段
5. 保留至少一个大牌(2或王)用于最后时刻
6. 你只有20张牌vs农民17张，要主动控制节奏

【关键原则】
- 能出多牌时绝不出单牌
- 能用普通牌压过就不用炸弹
- 失去控制时尽快夺回"""
        else:
            role_strategy = """【农民配合策略 - 生死攸关】
你是2v1，必须和队友配合！农民失败的最大原因是内斗！

【核心原则】
1. 队友出牌时 → 你99%情况要PASS！
2. 地主出牌时 → 有牌能压必须压！
3. 队友剩≤3张 → 出小牌帮队友先走
4. 地主剩≤3张 → 必须压制，绝对不能PASS！
5. 永远不要压队友的牌！互相压制=送分给地主！

【决策流程】
- 桌上是队友的牌 → PASS（让队友继续）
- 桌上是地主的牌 → 有牌就压（阻止地主）
- 两家农民都PASS → 地主免费获得出牌权=自杀

【记住】农民17张vs地主20张，配合好必赢，内斗必输！"""

        return f"""你是一个斗地主AI玩家。你是{self.name}，角色是{role}。

{role_strategy}

【工具使用原则】
可用工具:
{tools_list}

工具使用规则:
1. 只在复杂情况或不确定时调用工具
2. 简单情况直接出牌，不要浪费工具调用
3. 每个回合只能调用一个工具
4. 看到【工具结果】后必须立即出牌

【重要 - 你是决策者，工具只是顾问】
使用流程:
  1. 调用工具获取分析 (TOOL: xxx)
  2. 阅读工具返回的建议和理由
  3. 结合当前局势，用你的判断选择最佳方案
  4. 给出你的最终决策 (回答: xxx)

可用工具:
  TOOL: get_direct_recommendation  (获取局势分析与建议方案)
  TOOL: find_best_play             (获取弃牌效率分析)
  TOOL: get_valid_moves            (列出所有合法选项)

⚠️ 关键提醒: 工具提供建议，但决策权在你！
   不要机械复制，要理解分析后做出最佳选择"""
    
    def build_prompt(self, player: Player, game_state: GameState,
                     card_tracker: Optional[CardTracker] = None,
                     is_retry: bool = False, error_msg: str = "",
                     tool_result: str = None,  # If provided, agent must play cards
                     phase: str = "decide"   # "decide" (can call tool) or "after_tool" (must play)
                     ) -> str:
        hand_str = player.get_cards_string()
        is_landlord = player.is_landlord
        role = "地主" if is_landlord else "农民"

        lines = []

        # Phase 2: After tool result - agent must play cards
        if phase == "after_tool" and tool_result:
            lines.extend([
                "【工具结果】",
                tool_result,
                "",
                "=" * 40,
                "",
            ])

            # Include error message if this is a retry after invalid play
            if is_retry and error_msg:
                lines.extend([
                    "⚠️ 错误修正:",
                    f"  {error_msg}",
                    "",
                ])

            # Add game history
            history_str = self._format_game_history(game_state, player.name)
            if history_str:
                lines.append(history_str)
                lines.append("")

            lines.extend([
                "⚠️ 工具结果已提供，请直接给出最终出牌:",
                f"你的手牌: {hand_str}",
                f"当前局势: {self._format_table(game_state)}",
                f"你的角色: {role}",
                "",
            ])

            # Add opponent info for context
            opponents = game_state.get_opponents_info(player.name)
            for name, remaining, role_str in opponents:
                if remaining <= 3:
                    lines.append(f"⚠️ 注意: {name}({role_str})只剩{remaining}张牌！")

            lines.extend([
                "",
                "【策略指导】",
            ])

            if is_landlord:
                lines.extend([
                    "地主策略:",
                    "- 优先选择能出多张牌的选项（顺子/连对/对子 > 单牌）",
                    "- 农民快赢时，考虑用炸弹阻止",
                    "- 不要浪费炸弹，除非紧急情况",
                ])
            else:
                # Check who played last
                last_player = game_state.last_player_name
                last_was_landlord = False
                for name, remaining, role_str in opponents:
                    if name == last_player and role_str == "地主":
                        last_was_landlord = True
                        break

                if last_was_landlord:
                    lines.extend([
                        "【农民应对地主出牌】",
                        "- 地主出牌，你有能压过的牌就压",
                        "- 地主快赢时，必须压过，绝对不能PASS",
                    ])
                else:
                    lines.extend([
                        "【农民配合队友出牌 - 关键】",
                        "- 队友出牌，你99%情况要PASS！",
                        "- 让队友继续控制，你保存实力",
                        "- ⚠️ 压队友=送分给地主！绝对不要！",
                    ])

            lines.extend([
                "",
                "【出牌格式 - 必须严格遵守】",
                "直接复制工具结果中的出牌代码",
                "  回答: ♥8♣8  (从列表中复制的出牌)",
                "  回答: PASS  (选择不要)",
                "",
                "⚠️ 警告: 必须从工具结果列表中选择，不要自己构造牌型！",
            ])
            return "\n".join(lines)

        # Phase 1: Initial decision - agent can call tool or play
        lines.extend([
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
            f"当前局势: {self._format_table(game_state)}",
            f"你的角色: {role}",
            "",
        ])

        # Add game history
        history_str = self._format_game_history(game_state, player.name)
        if history_str:
            lines.append(history_str)
            lines.append("")

        # Add obvious situation guidance to reduce unnecessary tool calls
        table_type = game_state.table_series.type
        hand_size = len(player.cards)

        # Get opponent info
        opponents = game_state.get_opponents_info(player.name)
        landlord_cards = 20
        farmer_cards = []
        for name, remaining, role_str in opponents:
            if role_str == "地主":
                landlord_cards = remaining
            else:
                farmer_cards.append(remaining)

        lines.append("【局势分析】")

        # Simple cases where no tool needed
        if table_type == CardType.INVALID:
            lines.append("你是首家，可以出任意有效牌型")
            if is_landlord:
                lines.append("💡 地主建议: 优先出顺子/连对快速减牌")
            else:
                lines.append("💡 农民建议: 观察队友手牌，配合出牌")
        else:
            lines.append(f"桌上有牌，需要压过: {game_state.table_series}")

        # Emergency warnings
        if is_landlord:
            min_farmer = min(farmer_cards) if farmer_cards else 17
            if min_farmer <= 2:
                lines.append(f"⚠️ 紧急: 农民只剩{min_farmer}张！必须全力压制！")
        else:
            if landlord_cards <= 2:
                lines.append(f"⚠️ 紧急: 地主只剩{landlord_cards}张！必须阻止！")
            teammate_cards = [c for c in farmer_cards if c != hand_size]
            if teammate_cards and min(teammate_cards) <= 2:
                lines.append(f"💡 提示: 队友只剩{min(teammate_cards)}张，考虑出小牌配合")

        lines.extend([
            "",
            "【可用工具】",
        ])

        for name, desc in self.AVAILABLE_TOOLS.items():
            lines.append(f"  {name}: {desc}")

        lines.extend([
            "",
            "【何时使用工具】",
            "✅ 分析: TOOL: get_direct_recommendation - 获取局势分析和建议",
            "✅ 效率: TOOL: find_best_play - 分析哪种出法丢弃最多牌",
            "✅ 选项: TOOL: get_valid_moves - 列出所有合法出牌选项",
            "❌ 直接出牌: 手牌很少(≤3张) / 明显只能PASS / 明显只有一个选择",
            "",
        ])

        if not is_landlord:
            lines.extend([
                "【农民配合要点 - 重要】",
                "1. 队友出牌时 → PASS！让队友继续控制",
                "2. 地主出牌时 → 有牌必须压！",
                "3. 队友剩≤3张 → 出小牌帮助队友",
                "4. 地主剩≤3张 → 必须压制，不能PASS",
                "5. ⚠️ 警告: 不要和队友互相压制！这是农民最大错误！",
                "",
            ])
        else:
            lines.extend([
                "【地主要点】",
                "1. 首家时 → 出顺子/连对减少手牌",
                "2. 被压时 → 能压回来就压，保持控制",
                "3. 农民快赢时 → 用炸弹阻止",
                "4. 永远不要浪费炸弹！",
                "",
            ])

        lines.extend([
            "【操作】",
            "选择:",
            "  1. 调用工具 (格式: TOOL: tool_name) - 获取帮助",
            "  2. 直接出牌 (格式: 回答: ♠3♣3) - 你已确定要出的牌",
            "  3. PASS (格式: 回答: PASS) - 选择不要",
            "",
        ])

        if is_retry:
            lines.append(f"⚠️ 错误修正: {error_msg}")
            lines.append("")

        lines.append("请做出你的选择:")

        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌，你是首家"
        return f"桌上有 {game_state.table_series} (需压过此牌)"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        """
        Parse response to detect tool calls or card plays.
        """
        original_response = response.strip()
        response_upper = original_response.upper()
        
        # Check for TOOL call
        tool_match = re.search(r'(?:TOOL[:：]|工具[:：]|调用[:：]|使用[:：])\s*(\S+)', original_response, re.IGNORECASE)
        if tool_match:
            tool_name = tool_match.group(1).strip().lower()
            # Validate tool name
            available_tools_lower = {k.lower(): k for k in self.AVAILABLE_TOOLS.keys()}
            if tool_name in available_tools_lower:
                return False, original_response, [], ToolCall(available_tools_lower[tool_name])
            # Try fuzzy match
            for avail_lower, avail_orig in available_tools_lower.items():
                if avail_lower in tool_name or tool_name in avail_lower:
                    return False, original_response, [], ToolCall(avail_orig)
        
        # Check for PASS in answer section
        for marker in ['回答:', '回答：', 'answer:', '最终决定:', '出牌:', '出牌：']:
            if marker in original_response.lower():
                answer_part = original_response.lower().split(marker, 1)[-1].strip()
                if answer_part in ["pass", "不出", "不要", "过", "p", ""]:
                    return True, original_response, [], None
                break
        
        # Check whole response for PASS
        if original_response.upper() in ["PASS", "不出", "不要", "过", "P", ""]:
            return True, original_response, [], None
        
        # Parse cards from answer section
        cards = []
        answer_content = original_response
        
        # Try to extract answer section
        for marker in ['回答:', '回答：', 'answer:', 'answer：', '最终决定:', '出牌:', '出牌：']:
            if marker in original_response.lower():
                answer_content = original_response.split(marker, 1)[-1].strip()
                break
        
        # Parse cards
        suited_pattern = r'[♠♥♣♦](?:10|[2-9JQKA])'
        suited_matches = re.findall(suited_pattern, answer_content)
        cards.extend(suited_matches)
        
        if '小王' in answer_content:
            cards.append('小王')
        if '大王' in answer_content:
            cards.append('大王')
        
        return False, original_response, cards, None


class FullAgent(BaseAgent):
    """
    Full Agent: CoT + Tool Calling + Guide Reading
    """
    
    AVAILABLE_TOOLS = {
        "get_valid_moves": "获取所有合法出牌选项",
        "suggest_strategic_move": "获取AI策略建议", 
        "analyze_win_probability": "分析当前胜率",
        "get_played_cards": "查看已出牌历史",
        "search_optimal_path": "搜索最优出牌路径",
    }
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None,
                 guide_content: Optional[str] = None):
        super().__init__(name, config or AgentConfig(
            use_cot=True, 
            use_tools=True, 
            use_guide=True
        ))
        self.guide_content = guide_content or ""
    
    def get_system_prompt(self, is_landlord: bool) -> str:
        role = "地主" if is_landlord else "农民"
        tools_list = "\n".join([f"  - {name}: {desc}" for name, desc in self.AVAILABLE_TOOLS.items()])
        
        guide_section = ""
        if self.guide_content:
            guide_section = f"\n\n【策略指南】\n{self.guide_content[:500]}"
        
        return f"""你是一个高级斗地主AI玩家。你是{self.name}，角色是{role}。

【工具调用功能】
你有以下工具可用:
{tools_list}{guide_section}

【使用规则】
规则1: 每个回合你只能:
  A) 调用一个工具 (格式: TOOL: tool_name)
  B) 直接出牌 (格式: 回答: ♠3♣3)

规则2: 当你看到【工具结果】后:
  - 必须立即给出最终答案
  - 不能再调用其他工具

【输出格式】
调用工具: TOOL: tool_name
直接出牌: 回答: ♠3♣3 或 回答: PASS"""
    
    def build_prompt(self, player: Player, game_state: GameState,
                     card_tracker: Optional[CardTracker] = None,
                     is_retry: bool = False, error_msg: str = "",
                     tool_result: str = None,
                     phase: str = "decide") -> str:
        hand_str = player.get_cards_string()
        
        # Phase 2: After tool result
        if phase == "after_tool" and tool_result:
            lines = [
                "【工具结果】",
                tool_result,
                "",
                "=" * 40,
            ]

            # Show error message if this is a retry
            if is_retry and error_msg:
                lines.extend([
                    "",
                    "⚠️ 错误修正:",
                    f"  {error_msg}",
                ])

            # Add game history
            history_str = self._format_game_history(game_state, player.name)
            if history_str:
                lines.append("")
                lines.append(history_str)

            lines.extend([
                "",
                f"你的手牌: {hand_str}",
                f"当前局势: {self._format_table(game_state)}",
                "",
                "⚠️ 工具结果已提供。请分析后给出最终出牌:",
                "",
                "格式:",
                "  观察: <对工具结果的分析>",
                "  思考: <你的决策理由>",
                "  回答: ♠3♣3 或 PASS",
            ])
            return "\n".join(lines)
        
        # Phase 1: Initial decision
        lines = [
            f"你的手牌: {hand_str} (共{len(player.cards)}张)",
            f"当前局势: {self._format_table(game_state)}",
            "",
        ]

        # Add game history
        history_str = self._format_game_history(game_state, player.name)
        if history_str:
            lines.append(history_str)
            lines.append("")

        lines.append("【可用工具】")

        for name, desc in self.AVAILABLE_TOOLS.items():
            lines.append(f"  {name}: {desc}")

        lines.extend([
            "",
            "【任务】",
            "选择以下之一:",
            "  1. 调用工具: TOOL: tool_name",
            "  2. 直接出牌: 回答: ♠3♣3 或 回答: PASS",
            "",
        ])

        if is_retry:
            lines.append(f"⚠️ 错误修正: {error_msg}")
            lines.append("")

        lines.append("请做出你的选择:")

        return "\n".join(lines)
    
    def _format_table(self, game_state: GameState) -> str:
        if game_state.table_series.type == CardType.INVALID:
            return "桌上无牌"
        return f"桌上有 {game_state.table_series}"
    
    def parse_response(self, response: str) -> Tuple[bool, str, List[str], Optional[ToolCall]]:
        """Parse response - same as ToolAgent"""
        return ToolAgent("").parse_response(response)


def create_agent(agent_type: str, name: str, **kwargs) -> BaseAgent:
    """Factory function to create agents by type"""
    agent_map = {
        "normal": NormalAgent,
        "guide": GuideAgent,
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
