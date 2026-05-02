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
    


class ValidMovesTool:
    """Tool for finding valid moves given current hand and table"""
    
    @staticmethod
    def get_valid_moves(player: Player, table_series: Series,
                        include_pass: bool = True,
                        game_state: GameState = None) -> ToolResult:
        """
        Get all valid moves for a player given the current table.

        Args:
            player: The player whose turn it is
            table_series: Current series on table
            include_pass: Whether to include PASS as an option
            game_state: Optional game state for role-based filtering

        Returns:
            ToolResult with list of valid moves
        """
        moves = ValidMovesTool._find_all_valid_moves(player.cards, table_series)

        lines = [f"你的手牌: {player.get_cards_string()}", ""]

        # Check role and table situation for farmers
        is_teammate_played = False
        if game_state and not player.is_landlord and table_series.type != CardType.INVALID:
            last_player = getattr(game_state, 'last_player_name', None)
            if last_player:
                for p in game_state.players:
                    if p.name == last_player and not p.is_landlord:
                        is_teammate_played = True
                        break

        if table_series.type == CardType.INVALID:
            lines.append("你是首家，可以出任意有效牌型:")
        else:
            lines.append(f"桌上牌型: {table_series}")

            # Special warning for farmers when teammate played
            if is_teammate_played:
                lines.append("")
                lines.append("🚨🚨🚨 重要提醒 🚨🚨🚨")
                lines.append("桌上牌是队友出的！农民绝对不能压队友！")
                lines.append("压队友 = 帮地主 = 农民必输！")
                lines.append("👉 正确选择: PASS")
                lines.append("")
                lines.append("【虽然技术上你可以出以下牌，但绝对不要选】:")
            else:
                lines.append("你可以出的牌（必须压过桌上）:")

        if not moves:
            lines.append("  无有效出牌，建议PASS")
        else:
            for i, (cards, series) in enumerate(moves[:15], 1):  # Limit to 15 moves
                card_str = "".join([str(c) for c in cards])
                if is_teammate_played:
                    lines.append(f"  {i}. {series} -> 出牌: {card_str} ❌ 不要选！会压队友！")
                else:
                    lines.append(f"  {i}. {series} -> 出牌: {card_str}")

        if include_pass and table_series.type != CardType.INVALID:
            if is_teammate_played:
                lines.append("  ✅ PASS. 不出 (这是正确选择！让队友继续控制)")
            else:
                lines.append("  PASS. 不出")

        lines.append("")
        if is_teammate_played:
            lines.append("【建议】农民应该PASS，不要压队友")
        else:
            lines.append("【提示】从上面的列表中选择一项，复制出牌代码")

        return ToolResult(
            tool_name="get_valid_moves",
            result="\n".join(lines),
            data={
                "hand": player.get_cards_string(),
                "valid_moves": [(str(series), [str(c) for c in cards]) for cards, series in moves],
                "can_pass": include_pass and table_series.type != CardType.INVALID,
                "total_moves": len(moves),
                "is_teammate_played": is_teammate_played
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
        is_landlord = player.is_landlord

        # Analyze hand
        analysis = ValidMovesTool._analyze_hand(hand)
        has_bomb = analysis['bombs'] > 0
        has_rocket = analysis['jokers'] == 2

        lines = ["【手牌分析】"]
        lines.append(f"手牌数量: {len(hand)}张")
        lines.append(f"控制牌: 王={analysis['jokers']}, 2={analysis['twos']}, A={analysis['aces']}")
        lines.append(f"炸弹: {analysis['bombs']}个 {'(含火箭)' if has_rocket else ''}")

        # Get valid moves
        valid_moves = ValidMovesTool._find_all_valid_moves(hand, table)
        can_play_anything = table.type == CardType.INVALID

        # Strategy based on role and situation
        lines.append("\n【具体建议】")

        if len(hand) <= 3:
            lines.append("⚡ 快出完了！优先出单牌或对子，尽快结束游戏。")
            if has_bomb and len(hand) == 4:
                lines.append("💣 注意: 你有炸弹，但4张牌时优先出完而不是用炸弹！")

        elif is_landlord:
            # Landlord strategy
            if can_play_anything:
                lines.append("你是地主且首家出牌:")
                # Check for good straights
                straights = [m for m in valid_moves if m[1].type == CardType.STRAIGHT]
                pairs = [m for m in valid_moves if m[1].type == CardType.PAIR]

                if straights:
                    lines.append("  ✅ 优先出顺子(5+连续单牌)，快速减少手牌数量")
                if pairs and len(pairs) >= 3:
                    lines.append("  ✅ 有多个对子时，可出连对(3+连续对子)")
                lines.append("  ❌ 不要浪费炸弹！只有被压过或关键时刻才用")
                if has_bomb or has_rocket:
                    lines.append("  💣 炸弹/王炸留到最后或关键时刻")
            else:
                # Need to beat table
                can_beat_table = len(valid_moves) > 0
                if not can_beat_table:
                    lines.append("无法压过，建议PASS，保存实力")
                else:
                    lines.append("地主需要压过农民的牌:")
                    # Check if opponent is about to win
                    opponent_min = min(len(p.cards) for p in game_state.players if not p.is_landlord)
                    if opponent_min <= 3:
                        lines.append(f"  ⚠️ 农民只剩{opponent_min}张！必须压制，不能PASS")
                        if has_bomb:
                            lines.append("  💣 可考虑用炸弹阻止农民")
                    else:
                        lines.append("  ✅ 能用普通牌压过就不用炸弹")
                        lines.append("  ❌ 不要为了面子压牌，保留牌力更重要")

        else:
            # Farmer strategy
            landlord = next((p for p in game_state.players if p.is_landlord), None)
            landlord_cards = len(landlord.cards) if landlord else 20
            teammate = next((p for p in game_state.players if not p.is_landlord and p.name != player.name), None)
            teammate_cards = len(teammate.cards) if teammate else 17

            if can_play_anything:
                lines.append("【农民首家出牌策略】")

                if teammate_cards <= 3:
                    lines.append(f"🚨 队友只剩{teammate_cards}张！必须出最小牌帮助队友")
                    lines.append("   例: 有♠3就出♠3，有对子♠3♥3就出对子")
                elif landlord_cards <= 3:
                    lines.append(f"⚠️ 地主只剩{landlord_cards}张！必须出大牌阻止")
                    lines.append("   不能出小牌，要用大牌压制地主")
                else:
                    lines.append("💡 正常情况: 出中等牌，保留大牌应对地主")
                    lines.append("   目标是消耗地主，同时保存实力")

            else:
                # Need to beat table
                can_beat = len(valid_moves) > 0
                if not can_beat:
                    lines.append("【无法压过】")
                    lines.append("PASS保存大牌，等待更好的机会")
                else:
                    # Check who played the current table series
                    last_player_name = getattr(game_state, 'last_player_name', None)
                    last_was_landlord = False
                    if last_player_name:
                        for p in game_state.players:
                            if p.name == last_player_name:
                                last_was_landlord = p.is_landlord
                                break

                    if last_player_name and not last_was_landlord:
                        # Teammate played
                        lines.append("【队友出牌 - 配合策略】")
                        lines.append(f"队友剩{teammate_cards}张，你剩{len(hand)}张")

                        if teammate_cards <= 3 and len(hand) > teammate_cards + 5:
                            # Teammate is close to winning and you have many cards
                            lines.append("🚨 队友快赢了！你PASS让队友出完")
                            lines.append("   不要压队友，保存实力等下一轮")
                        elif teammate_cards <= len(hand):
                            # Teammate has fewer cards
                            lines.append("✅ 队友牌更少，你PASS让队友主导")
                            lines.append("   除非地主压了队友，否则不要出牌")
                        else:
                            # You have fewer cards
                            lines.append("💡 你牌更少，可以考虑压过队友接管")
                            lines.append("   但要用中等牌，不要浪费最大牌")

                        lines.append("⚠️ 警告: 农民之间互相压制=给地主送分！")

                    else:
                        # Landlord played
                        lines.append("【地主出牌 - 应对策略】")

                        if landlord_cards <= 2:
                            lines.append(f"🚨 地主只剩{landlord_cards}张！必须压过！")
                            lines.append("   有牌必须出，不能PASS！")
                            if has_bomb:
                                lines.append("   💣 必要时用炸弹阻止地主！")
                        elif landlord_cards <= 5:
                            lines.append(f"⚠️ 地主只剩{landlord_cards}张！尽量压过")
                            lines.append("   不让地主轻松出完")
                        else:
                            lines.append("💡 地主还有牌，能用中等牌压过就不用最大牌")
                            lines.append("   保存实力，持续给地主压力")

        return ToolResult(
            tool_name="suggest_strategic_move",
            result="\n".join(lines),
            data=analysis
        )

    @staticmethod
    def get_direct_recommendation(player: Player, game_state: GameState) -> ToolResult:
        """
        Get an advisory recommendation for what to play.
        This tool provides analysis and guidance, but lets the agent make the final decision.
        """
        hand = player.cards
        table = game_state.table_series
        is_landlord = player.is_landlord

        # Get all valid moves
        valid_moves = ValidMovesTool._find_all_valid_moves(hand, table)

        # Get opponent info
        landlord = next((p for p in game_state.players if p.is_landlord), None)
        landlord_cards = len(landlord.cards) if landlord else 20
        teammate = next((p for p in game_state.players if not p.is_landlord and p.name != player.name), None)
        teammate_cards = len(teammate.cards) if teammate else 17

        lines = ["【局势分析与建议】"]
        lines.append("")

        # Check if need to beat table
        last_player_name = None
        last_was_landlord = False
        if table.type != CardType.INVALID:
            last_player_name = getattr(game_state, 'last_player_name', None)
            if last_player_name:
                for p in game_state.players:
                    if p.name == last_player_name:
                        last_was_landlord = p.is_landlord
                        break

        # Farmer facing teammate's play
        if not is_landlord and not last_was_landlord and table.type != CardType.INVALID:
            lines.append("【关键判断 - 队友出牌】")
            lines.append(f"桌上牌由队友 {last_player_name} 打出")
            lines.append("")
            lines.append("【农民配合原则】")
            lines.append("✅ 正确做法: PASS")
            lines.append("   - 让队友继续控制出牌权")
            lines.append("   - 保存实力，等待地主出牌时再压制")
            lines.append("   - 农民互相压制 = 帮地主获胜")
            lines.append("")
            lines.append("❌ 错误做法: 压队友的牌")
            lines.append("   这会浪费大牌，让地主白获得出牌权")
            lines.append("")
            lines.append("【你的选择】")
            lines.append("应该PASS，不要选任何出牌")
            return ToolResult(
                tool_name="get_direct_recommendation",
                result="\n".join(lines),
                data={"advice": "PASS", "reason": "teammate_played"}
            )

        # Need to beat table
        if table.type != CardType.INVALID:
            if not valid_moves:
                lines.append("【局势分析】")
                lines.append(f"桌上牌型: {table}")
                lines.append("你的手牌无法压过此牌型")
                lines.append("")
                lines.append("【建议】")
                lines.append("✅ 选择 PASS（不出）")
                lines.append("   保存实力，等待更好的机会")
                return ToolResult(
                    tool_name="get_direct_recommendation",
                    result="\n".join(lines),
                    data={"advice": "PASS", "reason": "cannot_beat"}
                )

            # Landlord or Farmer vs Landlord
            if not is_landlord and landlord_cards <= 2:
                # Emergency: landlord about to win
                lines.append("【紧急局势】")
                lines.append(f"⚠️ 地主只剩 {landlord_cards} 张牌！")
                lines.append(f"桌上牌型: {table}")
                lines.append("")
                lines.append("【可选压制方案】")
                # Show top 3 options sorted by value (descending)
                sorted_moves = sorted(valid_moves, key=lambda x: x[1].cards[0].value if x[1].cards else 0, reverse=True)
                for i, (cds, srs) in enumerate(sorted_moves[:3], 1):
                    c_str = "".join([str(c) for c in cds])
                    lines.append(f"  {i}. {c_str} ({srs})")
                lines.append("")
                lines.append("【建议】")
                lines.append("地主快赢了，必须压制！")
                lines.append("优先使用最大能压过的牌")
                lines.append("从上述方案中选择")
                return ToolResult(
                    tool_name="get_direct_recommendation",
                    result="\n".join(lines),
                    data={"advice": "use_biggest", "reason": "landlord_emergency"}
                )
            else:
                # Normal: use medium cards
                lines.append("【局势分析】")
                lines.append(f"桌上牌型: {table}")
                lines.append(f"地主剩牌: {landlord_cards}张")
                lines.append("")
                lines.append("【可选方案】")
                # Show options sorted by value (ascending)
                sorted_moves = sorted(valid_moves, key=lambda x: x[1].cards[0].value if x[1].cards else 0)
                for i, (cds, srs) in enumerate(sorted_moves[:3], 1):
                    c_str = "".join([str(c) for c in cds])
                    lines.append(f"  {i}. {c_str} ({srs})")
                lines.append("")
                lines.append("【建议】")
                lines.append("能用中等牌压过就不用最大牌")
                lines.append("保留大牌应对关键时刻")
                lines.append("从上述方案中选择")
                return ToolResult(
                    tool_name="get_direct_recommendation",
                    result="\n".join(lines),
                    data={"advice": "use_medium", "reason": "efficient_beat"}
                )

        # Table is empty - we're first to play
        if not valid_moves:
            lines.append("【异常】无牌可出")
            return ToolResult(
                tool_name="get_direct_recommendation",
                result="\n".join(lines),
                data={"advice": "PASS", "reason": "no_moves"}
            )

        # First to play - show options by type
        straights = [m for m in valid_moves if m[1].type == CardType.STRAIGHT]
        pairs = [m for m in valid_moves if m[1].type == CardType.PAIR]
        triples = [m for m in valid_moves if m[1].type == CardType.TRIPLE]
        singles = [m for m in valid_moves if m[1].type == CardType.SINGLE]

        lines.append("【你是首家，可出任意牌型】")
        lines.append("")

        if is_landlord:
            lines.append("【地主打法建议】")
            lines.append("优先出能多张牌的牌型，快速减牌:")
            if straights:
                best = max(straights, key=lambda x: len(x[0]))
                card_str = "".join([str(c) for c in best[0]])
                lines.append(f"  - 顺子: {card_str} (出{len(best[0])}张)")
            if triples:
                card_str = "".join([str(c) for c in triples[0][0]])
                lines.append(f"  - 三带: {card_str} (出{len(triples[0][0])}张)")
            if pairs:
                sorted_pairs = sorted(pairs, key=lambda x: x[1].cards[0].value)
                card_str = "".join([str(c) for c in sorted_pairs[0][0]])
                lines.append(f"  - 对子: {card_str} (出2张)")
            if singles:
                sorted_singles = sorted(singles, key=lambda x: x[1].cards[0].value)
                card_str = "".join([str(c) for c in sorted_singles[0][0]])
                lines.append(f"  - 单牌: {card_str} (出1张)")
            lines.append("")
            lines.append("【建议】")
            lines.append("地主需要快速减牌，优先出多张牌型")
        else:
            lines.append("【农民打法建议】")
            if teammate_cards <= 3:
                lines.append(f"🚨 队友只剩{teammate_cards}张！出最小牌帮助队友:")
                if singles:
                    sorted_singles = sorted(singles, key=lambda x: x[1].cards[0].value)
                    card_str = "".join([str(c) for c in sorted_singles[0][0]])
                    lines.append(f"  最小单牌: {card_str}")
            elif landlord_cards <= 3:
                lines.append(f"⚠️ 地主只剩{landlord_cards}张！必须出牌阻止:")
                if straights:
                    best = max(straights, key=lambda x: len(x[0]))
                    card_str = "".join([str(c) for c in best[0]])
                    lines.append(f"  顺子: {card_str} (快速出多张)")
            else:
                lines.append("💡 正常情况: 出中等牌，保留大牌应对地主")
                if singles:
                    sorted_singles = sorted(singles, key=lambda x: x[1].cards[0].value)
                    idx = len(sorted_singles) // 3
                    best = sorted_singles[idx] if idx < len(sorted_singles) else sorted_singles[0]
                    card_str = "".join([str(c) for c in best[0]])
                    lines.append(f"  建议单牌: {card_str}")
            lines.append("")
            lines.append("【建议】")
            lines.append("根据队友和地主的牌数，选择合适策略")

        return ToolResult(
            tool_name="get_direct_recommendation",
            result="\n".join(lines),
            data={"advice": "analyze_and_choose", "reason": "first_to_play"}
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
    """Tree search tool for finding optimal card plays to empty hand"""

    @staticmethod
    def find_best_play(hand: List[Card], table_series: Series = None, is_landlord: bool = False) -> ToolResult:
        """
        Find the best play to minimize remaining cards.
        Uses greedy + lookahead to find plays that discard the most cards efficiently.

        Args:
            hand: Current hand
            table_series: Current series on table (if any)
            is_landlord: Whether player is landlord

        Returns:
            ToolResult with best play recommendation
        """
        if table_series is None:
            table_series = Series()

        # Get all valid moves
        all_moves = ValidMovesTool._find_all_valid_moves(hand, table_series)

        if not all_moves:
            if table_series.type != CardType.INVALID:
                return ToolResult(
                    tool_name="find_best_play",
                    result="无有效出牌，建议PASS",
                    data={"action": "PASS", "reason": "cannot_beat"}
                )
            return ToolResult(
                tool_name="find_best_play",
                result="无法出牌",
                data={"action": "PASS", "reason": "no_moves"}
            )

        # Score each move based on card reduction efficiency
        scored_moves = []
        for cards, series in all_moves:
            score = TreeSearchTool._score_move(cards, series, hand, is_landlord)
            scored_moves.append((score, cards, series))

        # Sort by score descending
        scored_moves.sort(key=lambda x: x[0], reverse=True)

        # Get best move
        best_score, best_cards, best_series = scored_moves[0]
        card_str = "".join([str(c) for c in best_cards])

        lines = ["【出牌方案分析】"]
        lines.append("")
        lines.append(f"当前手牌: {len(hand)}张")
        if table_series.type != CardType.INVALID:
            lines.append(f"桌上牌型: {table_series}")
        lines.append("")

        # Show top 3 options with analysis
        lines.append("【可选方案】（按效率排序）")
        for i, (score, cards, series) in enumerate(scored_moves[:3], 1):
            card_str_opt = "".join([str(c) for c in cards])
            efficiency = TreeSearchTool._get_score_reason(score, len(cards), is_landlord)
            lines.append(f"  {i}. {card_str_opt}")
            lines.append(f"     牌型: {series}")
            lines.append(f"     丢弃: {len(cards)}张，剩余: {len(hand) - len(cards)}张")
            lines.append(f"     分析: {efficiency}")
            lines.append("")

        lines.append("【选择建议】")
        lines.append(f"方案1 '{''.join([str(c) for c in scored_moves[0][2]])}' 丢弃最多({len(scored_moves[0][2])}张)，优先考虑")
        if len(scored_moves) > 1 and len(scored_moves[0][2]) == len(scored_moves[1][2]):
            lines.append(f"方案2 牌值更低，也可考虑")
        lines.append("")
        lines.append("请从上述方案中选择，或根据局势判断")

        return ToolResult(
            tool_name="find_best_play",
            result="\n".join(lines),
            data={
                "recommended_cards": card_str,
                "series": str(best_series),
                "cards_discarded": len(best_cards),
                "cards_remaining": len(hand) - len(best_cards),
                "alternatives": [{"cards": "".join([str(c) for c in cards]), "series": str(series)}
                                for _, cards, series in scored_moves[1:4]]
            }
        )

    @staticmethod
    def _score_move(cards: List[Card], series: Series, hand: List[Card], is_landlord: bool) -> float:
        """Score a move based on how good it is for emptying hand"""
        score = 0.0

        # Base: number of cards discarded (more is better)
        num_cards = len(cards)
        score += num_cards * 10  # 10 points per card

        # Bonus for multi-card plays
        if num_cards >= 5:  # Straight
            score += 20
        elif num_cards == 4 and series.type == CardType.BOMB:
            score += 15  # Bomb is powerful but save it
        elif num_cards >= 3:
            score += 10  # Triples, triple+single, etc.
        elif num_cards == 2:
            score += 5   # Pairs

        # Prefer lower value cards to save high cards
        max_value = max(c.value for c in cards) if cards else 0
        if max_value <= 5:  # 3-7
            score += 8
        elif max_value <= 8:  # 8-10
            score += 4
        elif max_value <= 11:  # J-A
            score += 0
        else:  # 2, jokers
            score -= 5  # Penalty for wasting high cards

        # Consider remaining hand after this play
        remaining = [c for c in hand if c not in cards]
        if remaining:
            # Check if remaining hand has good plays
            future_moves = ValidMovesTool._find_all_valid_moves(remaining, Series())
            if future_moves:
                # Can continue playing - good
                score += 5
            else:
                # Dead end - bad
                score -= 10

        # Landlord bonus for fast reduction
        if is_landlord:
            if num_cards >= 4:
                score += 5

        return score

    @staticmethod
    def _get_score_reason(score: float, num_cards: int, is_landlord: bool) -> str:
        """Generate human-readable reason for the score"""
        if num_cards >= 5:
            return f"顺子可一次出{num_cards}张牌，快速减少手牌数量"
        elif num_cards == 4:
            return "炸弹威力大，但只在必要时使用"
        elif num_cards >= 3:
            return f"三带/飞机可一次出{num_cards}张牌，效率较高"
        elif num_cards == 2:
            return "对子可出2张牌，比单牌效率高"
        else:
            if is_landlord:
                return "单牌出牌，保留大牌应对农民"
            else:
                return "单牌出牌，配合队友策略"


# Tool registry for easy access
TOOLS = {
    "get_played_cards": CardHistoryTool.get_played_cards,
    "get_remaining_deck": CardHistoryTool.get_remaining_deck,
    "get_valid_moves": ValidMovesTool.get_valid_moves,
    "get_direct_recommendation": ValidMovesTool.get_direct_recommendation,
    "find_best_play": TreeSearchTool.find_best_play,
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
        "get_direct_recommendation": "AI直接推荐最优出牌（考虑角色和局势）",
        "find_best_play": "搜索最优出牌（最大化弃牌数量）",
        "get_valid_moves": "列出所有合法出牌选项（带队友保护提示）",
        "get_played_cards": "查询已出牌历史",
        "get_remaining_deck": "查询剩余牌分布",
    }

    lines = ["可用工具:"]
    for name, desc in descriptions.items():
        lines.append(f"  - {name}: {desc}")

    return "\n".join(lines)
