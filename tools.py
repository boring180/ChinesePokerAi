"""
Tool Functions for AI Agents
Implements tool calling capabilities for advanced AI agents
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import itertools

from game_control import Player, Card, Series, CardType, validate_series, VALUES
from game_state import GameState, CardTracker


@dataclass
class ToolResult:
    """Result of a tool call"""
    tool_name: str
    result: str
    data: dict = None


class CardHistoryTool:
    """Tool for retrieving card play history"""
    
    @staticmethod
    def get_played_cards(game_state: GameState, player_name: Optional[str] = None) -> ToolResult:
        """
        Get all cards played by a specific player, or all played cards.
        
        Args:
            game_state: Current game state
            player_name: Player to query (None for all cards)
        
        Returns:
            ToolResult with formatted card history
        """
        if player_name:
            cards = game_state.get_played_cards_by_player(player_name)
            card_strs = [str(c) for c in cards]
            result_str = f"{player_name} 已出牌: {', '.join(card_strs) if card_strs else '无'}"
            return ToolResult(
                tool_name="get_played_cards",
                result=result_str,
                data={"player": player_name, "cards": card_strs, "count": len(cards)}
            )
        else:
            cards = game_state.get_all_played_cards()
            card_strs = [str(c) for c in cards]
            result_str = f"全局已出牌: {', '.join(card_strs) if card_strs else '无'}"
            return ToolResult(
                tool_name="get_played_cards",
                result=result_str,
                data={"cards": card_strs, "count": len(cards)}
            )
    
    @staticmethod
    def get_remaining_deck(game_state: GameState) -> ToolResult:
        """
        Get remaining cards in deck (not yet played).
        Useful for inferring what opponents might hold.
        """
        remaining = game_state.get_remaining_deck_composition()
        lines = ["剩余牌分布:"]
        for value, count in remaining.items():
            if count > 0:
                lines.append(f"  {value}: {count}张")
        
        return ToolResult(
            tool_name="get_remaining_deck",
            result="\n".join(lines),
            data=remaining
        )
    
    @staticmethod
    def get_opponent_estimates(game_state: GameState, opponent_name: str) -> ToolResult:
        """
        Get estimated card composition for an opponent.
        
        Args:
            game_state: Current game state
            opponent_name: Name of opponent to estimate
        """
        likely = game_state.get_likely_cards_for_player(opponent_name)
        lines = [f"{opponent_name} 手牌估计 ({game_state.get_remaining_cards_estimate(opponent_name)}张):"]
        for value, count in likely.items():
            if count > 0:
                lines.append(f"  {value}: 约{count}张")
        
        return ToolResult(
            tool_name="get_opponent_estimates",
            result="\n".join(lines),
            data=likely
        )
    
    @staticmethod
    def get_high_cards_remaining(game_state: GameState, card_tracker: CardTracker) -> ToolResult:
        """
        Get information about remaining high cards (10, J, Q, K, A, 2, Jokers).
        These are critical for control.
        """
        remaining_high = card_tracker.get_remaining_high_cards(game_state)
        lines = ["剩余高牌及可能持有者:"]
        for card_name, holders in remaining_high.items():
            lines.append(f"  {card_name}: 可能在 {', '.join(holders)} 手中")
        
        return ToolResult(
            tool_name="get_high_cards_remaining",
            result="\n".join(lines),
            data=remaining_high
        )


class ValidMovesTool:
    """Tool for finding valid moves given current hand and table"""
    
    @staticmethod
    def get_valid_moves(player: Player, table_series: Series, 
                        include_pass: bool = True) -> ToolResult:
        """
        Get all valid moves for a player given the current table.
        
        Args:
            player: The player whose turn it is
            table_series: Current series on table
            include_pass: Whether to include PASS as an option
        
        Returns:
            ToolResult with list of valid moves
        """
        moves = ValidMovesTool._find_all_valid_moves(player.cards, table_series)
        
        lines = [f"你的手牌: {player.get_cards_string()}", ""]
        
        if table_series.type == CardType.INVALID:
            lines.append("你是首家，可以出任意有效牌型:")
        else:
            lines.append(f"桌上牌型: {table_series}")
            lines.append("你可以出的牌（必须压过桌上）:")
        
        if not moves:
            lines.append("  无有效出牌，建议PASS")
        else:
            for i, (cards, series) in enumerate(moves[:15], 1):  # Limit to 15 moves
                lines.append(f"  {i}. {series}")
        
        if include_pass and table_series.type != CardType.INVALID:
            lines.append("  PASS. 不出")
        
        return ToolResult(
            tool_name="get_valid_moves",
            result="\n".join(lines),
            data={
                "hand": player.get_cards_string(),
                "valid_moves": [(str(series), [str(c) for c in cards]) for cards, series in moves],
                "can_pass": include_pass and table_series.type != CardType.INVALID,
                "total_moves": len(moves)
            }
        )
    
    @staticmethod
    def _find_all_valid_moves(hand: List[Card], table_series: Series) -> List[Tuple[List[Card], Series]]:
        """
        Find all valid moves from hand that can beat table_series.
        Returns list of (cards, series) tuples.
        """
        moves = []
        
        # Generate all possible series from hand
        from collections import defaultdict
        value_to_cards = defaultdict(list)
        for card in hand:
            value_to_cards[card.value].append(card)
        
        # Singles
        for card in hand:
            series = validate_series([card])
            if ValidMovesTool._can_play(series, table_series):
                moves.append(([card], series))
        
        # Pairs
        for value, cards in value_to_cards.items():
            if len(cards) >= 2:
                pair = cards[:2]
                series = validate_series(pair)
                if ValidMovesTool._can_play(series, table_series):
                    moves.append((pair, series))
        
        # Triples
        for value, cards in value_to_cards.items():
            if len(cards) >= 3:
                triple = cards[:3]
                series = validate_series(triple)
                if ValidMovesTool._can_play(series, table_series):
                    moves.append((triple, series))
                
                # Triple with single
                for kicker in hand:
                    if kicker not in triple:
                        combo = triple + [kicker]
                        series = validate_series(combo)
                        if ValidMovesTool._can_play(series, table_series):
                            moves.append((combo, series))
                
                # Triple with pair (if 4 cards)
                if len(cards) == 4:
                    combo = cards  # All 4 as triple+pair
                    series = validate_series(combo)
                    if ValidMovesTool._can_play(series, table_series):
                        moves.append((combo, series))
        
        # Bombs (4 of a kind)
        for value, cards in value_to_cards.items():
            if len(cards) == 4:
                series = validate_series(cards)
                if ValidMovesTool._can_play(series, table_series):
                    moves.append((cards, series))
        
        # Rocket (both jokers)
        jokers = [c for c in hand if c.value >= 13]
        if len(jokers) == 2:
            series = validate_series(jokers)
            if ValidMovesTool._can_play(series, table_series):
                moves.append((jokers, series))
        
        # Straights (5+)
        sorted_hand = sorted(hand, key=lambda c: c.value)
        for length in range(5, len(sorted_hand) + 1):
            for start in range(len(sorted_hand) - length + 1):
                subset = sorted_hand[start:start + length]
                if subset[-1].value < 12:  # Not ending with 2
                    series = validate_series(subset)
                    if series.type == CardType.STRAIGHT and ValidMovesTool._can_play(series, table_series):
                        moves.append((subset, series))
        
        return moves
    
    @staticmethod
    def _can_play(series: Series, table: Series) -> bool:
        """Check if series can be played on table"""
        if series.type == CardType.INVALID:
            return False
        can_beat, _ = series.can_beat(table)
        return can_beat
    
    @staticmethod
    def suggest_strategic_move(player: Player, game_state: GameState) -> ToolResult:
        """
        Suggest a strategic move based on hand analysis.
        Considers card count, control cards, and game situation.
        """
        hand = player.cards
        table = game_state.table_series
        
        # Analyze hand
        analysis = ValidMovesTool._analyze_hand(hand)
        
        lines = ["手牌分析:", f"  总数: {len(hand)}张"]
        lines.append(f"  大牌: 王={analysis['jokers']}, 2={analysis['twos']}, A={analysis['aces']}")
        lines.append(f"  炸弹: {analysis['bombs']}个")
        lines.append(f"  顺子/连对潜力: {'是' if analysis['has_straight_potential'] else '否'}")
        
        # Strategy suggestion
        if len(hand) <= 3:
            lines.append("\n策略: 你快赢了，尽快出完！优先单牌或对子。")
        elif analysis['control_strong']:
            lines.append("\n策略: 控制力强，可主动出牌控制节奏。考虑出顺子快速减牌。")
        else:
            lines.append("\n策略: 控制力弱，建议配合队友，保留大牌应对地主。")
        
        return ToolResult(
            tool_name="suggest_strategic_move",
            result="\n".join(lines),
            data=analysis
        )
    
    @staticmethod
    def _analyze_hand(hand: List[Card]) -> dict:
        """Analyze hand composition"""
        values = [c.value for c in hand]
        from collections import Counter
        counts = Counter(values)
        
        return {
            'jokers': counts.get(13, 0) + counts.get(14, 0),
            'twos': counts.get(12, 0),
            'aces': counts.get(11, 0),
            'bombs': sum(1 for c in counts.values() if c == 4),
            'has_straight_potential': len(hand) >= 5 and max(values) - min(values) >= 4,
            'control_strong': (counts.get(12, 0) + counts.get(13, 0) + counts.get(14, 0)) >= 2
        }


class TreeSearchTool:
    """Tool for tree search to find optimal card playing sequence"""
    
    @staticmethod
    def search_optimal_path(hand: List[Card], max_depth: int = 5) -> ToolResult:
        """
        Search for optimal sequence to empty hand.
        Uses simple greedy + lookahead strategy.
        
        Args:
            hand: Current hand
            max_depth: Search depth (number of future plays)
        
        Returns:
            ToolResult with suggested playing sequence
        """
        sequences = TreeSearchTool._find_play_sequences(hand, max_depth)
        
        if not sequences:
            return ToolResult(
                tool_name="search_optimal_path",
                result="无法找到有效出牌序列",
                data={}
            )
        
        # Score sequences (fewer moves = better)
        best = min(sequences, key=lambda x: x['moves'])
        
        lines = [f"搜索深度: {max_depth}", f"找到 {len(sequences)} 种出牌方案", ""]
        lines.append(f"最优方案 (预计{best['moves']}回合出完):")
        for i, play in enumerate(best['sequence'][:5], 1):
            lines.append(f"  {i}. {play}")
        
        return ToolResult(
            tool_name="search_optimal_path",
            result="\n".join(lines),
            data=best
        )
    
    @staticmethod
    def _find_play_sequences(hand: List[Card], max_depth: int) -> List[dict]:
        """Find possible play sequences to empty hand"""
        sequences = []
        
        def recursive_search(current_hand: List[Card], current_sequence: List[str], depth: int):
            if not current_hand:
                sequences.append({
                    'moves': len(current_sequence),
                    'sequence': current_sequence[:]
                })
                return
            
            if depth >= max_depth:
                return
            
            # Find all possible plays
            moves = ValidMovesTool._find_all_valid_moves(current_hand, Series())
            
            # Prioritize: big combinations > small plays
            moves.sort(key=lambda x: len(x[0]), reverse=True)
            
            for cards, series in moves[:5]:  # Limit branching factor
                new_hand = [c for c in current_hand if c not in cards]
                current_sequence.append(str(series))
                recursive_search(new_hand, current_sequence, depth + 1)
                current_sequence.pop()
        
        recursive_search(hand, [], 0)
        return sequences
    
    @staticmethod
    def analyze_win_probability(player: Player, game_state: GameState) -> ToolResult:
        """
        Estimate win probability based on current state.
        
        Args:
            player: The player to analyze
            game_state: Current game state
        
        Returns:
            ToolResult with probability assessment
        """
        hand_size = len(player.cards)
        analysis = ValidMovesTool._analyze_hand(player.cards)
        
        # Simple heuristic scoring
        score = 0
        
        # Card count advantage
        min_opponent = min(len(p.cards) for p in game_state.players if p.name != player.name)
        if hand_size < min_opponent:
            score += 20
        
        # Control cards
        score += analysis['jokers'] * 15
        score += analysis['twos'] * 10
        score += analysis['bombs'] * 25
        
        # Combinations reduce hand faster
        score += analysis.get('straights', 0) * 5
        
        # Role bonus
        is_landlord = player.is_landlord
        if is_landlord:
            score += 10  # Landlord advantage
        
        probability = min(95, max(5, 40 + score))
        
        lines = [
            f"胜率评估: {probability}%",
            f"评估因素:",
            f"  - 手牌数量: {hand_size} ({'优势' if hand_size < min_opponent else '劣势'})",
            f"  - 控制力: 王{analysis['jokers']} 2点{analysis['twos']} A{analysis['aces']}",
            f"  - 炸弹: {analysis['bombs']}个",
            f"  - 角色: {'地主' if is_landlord else '农民'}",
        ]
        
        return ToolResult(
            tool_name="analyze_win_probability",
            result="\n".join(lines),
            data={
                "probability": probability,
                "hand_size": hand_size,
                "control_score": analysis['jokers'] * 15 + analysis['twos'] * 10,
                "bomb_count": analysis['bombs']
            }
        )


# Tool registry for easy access
TOOLS = {
    "get_played_cards": CardHistoryTool.get_played_cards,
    "get_remaining_deck": CardHistoryTool.get_remaining_deck,
    "get_opponent_estimates": CardHistoryTool.get_opponent_estimates,
    "get_high_cards_remaining": CardHistoryTool.get_high_cards_remaining,
    "get_valid_moves": ValidMovesTool.get_valid_moves,
    "suggest_strategic_move": ValidMovesTool.suggest_strategic_move,
    "search_optimal_path": TreeSearchTool.search_optimal_path,
    "analyze_win_probability": TreeSearchTool.analyze_win_probability,
}


def execute_tool(tool_name: str, **kwargs) -> ToolResult:
    """
    Execute a tool by name.
    
    Args:
        tool_name: Name of the tool to execute
        **kwargs: Arguments for the tool
    
    Returns:
        ToolResult from the tool execution
    """
    if tool_name not in TOOLS:
        return ToolResult(
            tool_name=tool_name,
            result=f"错误: 未知工具 '{tool_name}'",
            data={}
        )
    
    try:
        return TOOLS[tool_name](**kwargs)
    except Exception as e:
        return ToolResult(
            tool_name=tool_name,
            result=f"工具执行错误: {str(e)}",
            data={}
        )


def get_tool_descriptions() -> str:
    """Get descriptions of all available tools"""
    descriptions = {
        "get_played_cards": "查询某个玩家或全局已出的牌",
        "get_remaining_deck": "查询牌堆中剩余的牌分布",
        "get_opponent_estimates": "估算对手可能的手牌组成",
        "get_high_cards_remaining": "查询剩余高牌及可能持有者",
        "get_valid_moves": "获取当前所有有效出牌选项",
        "suggest_strategic_move": "获取基于手牌分析的策略建议",
        "search_optimal_path": "搜索最快出完手牌的出牌序列",
        "analyze_win_probability": "评估当前胜率",
    }
    
    lines = ["可用工具:"]
    for name, desc in descriptions.items():
        lines.append(f"  - {name}: {desc}")
    
    return "\n".join(lines)
