"""
Game State Management for AI Observation
Tracks all observable information for AI agents
"""

from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from game_control import Player, Card, Series, CardType, VALUES


@dataclass
class PlayRecord:
    """Record of a single play"""
    player_name: str
    series: Series
    turn_number: int
    is_pass: bool = False


@dataclass  
class GameState:
    """
    Observable game state for AI agents.
    Tracks everything an AI can observe during gameplay.
    """
    # Players
    players: List[Player] = field(default_factory=list)
    
    # Current game info
    current_player_idx: int = 0
    landlord_idx: int = 0
    turn_count: int = 0
    
    # Table state
    table_series: Series = field(default_factory=Series)
    last_player_name: Optional[str] = None
    consecutive_passes: int = 0
    
    # History
    play_history: List[PlayRecord] = field(default_factory=list)
    
    # Card tracking
    played_cards: List[Card] = field(default_factory=list)
    
    # Per-player tracking
    _player_played_cards: Dict[str, List[Card]] = field(default_factory=lambda: defaultdict(list))
    _player_remaining_counts: Dict[str, int] = field(default_factory=dict)
    
    def initialize(self, players: List[Player], landlord_idx: int):
        """Initialize game state with players"""
        self.players = players
        self.landlord_idx = landlord_idx
        self.current_player_idx = landlord_idx  # Landlord starts
        
        for p in players:
            self._player_remaining_counts[p.name] = len(p.cards)
    
    def record_play(self, player_name: str, series: Series, is_pass: bool = False):
        """Record a play in history"""
        self.turn_count += 1
        record = PlayRecord(
            player_name=player_name,
            series=series,
            turn_number=self.turn_count,
            is_pass=is_pass
        )
        self.play_history.append(record)
        
        if not is_pass:
            self.played_cards.extend(series.cards)
            self._player_played_cards[player_name].extend(series.cards)
            self.table_series = series
            self.last_player_name = player_name
            self.consecutive_passes = 0
        else:
            self.consecutive_passes += 1
        
        # Update remaining counts
        for p in self.players:
            self._player_remaining_counts[p.name] = len(p.cards)
    
    def clear_table(self):
        """Clear the table (new round)"""
        self.table_series = Series()
        self.last_player_name = None
        self.consecutive_passes = 0
    
    def next_player(self):
        """Advance to next player"""
        self.current_player_idx = (self.current_player_idx + 1) % 3
    
    def get_player_role(self, player_name: str) -> str:
        """Get player's role (landlord/farmer)"""
        player = self._get_player_by_name(player_name)
        return "地主" if player.is_landlord else "农民"
    
    def get_player_by_idx(self, idx: int) -> Player:
        """Get player by index"""
        return self.players[idx]
    
    def _get_player_by_name(self, name: str) -> Player:
        """Get player by name"""
        for p in self.players:
            if p.name == name:
                return p
        raise ValueError(f"Player {name} not found")
    
    def get_remaining_cards_estimate(self, player_name: str) -> int:
        """Get estimated remaining cards for a player"""
        return self._player_remaining_counts.get(player_name, 17)
    
    def get_played_cards_by_player(self, player_name: str) -> List[Card]:
        """Get all cards played by a specific player"""
        return self._player_played_cards.get(player_name, [])
    
    def get_all_played_cards(self) -> List[Card]:
        """Get all cards played so far"""
        return self.played_cards.copy()
    
    def get_remaining_deck_composition(self) -> Dict[str, int]:
        """
        Get composition of remaining cards in deck (not yet played)
        Returns count per value
        """
        all_cards = set(range(15))  # All card values
        played_values = defaultdict(int)
        
        for card in self.played_cards:
            played_values[card.value] += 1
        
        # Total counts per value
        total_per_value = {
            13: 1,  # Small joker
            14: 1,  # Big joker
        }
        for v in range(13):  # 3 through 2
            total_per_value[v] = 4
        
        remaining = {}
        for v in range(15):
            remaining[VALUES[v]] = total_per_value.get(v, 0) - played_values.get(v, 0)
        
        return remaining
    
    def get_likely_cards_for_player(self, player_name: str) -> Dict[str, int]:
        """
        Estimate likely card composition for a player.
        Based on their played cards and what's left in deck.
        """
        remaining = self.get_remaining_deck_composition()
        player_played = defaultdict(int)
        
        for card in self._player_played_cards.get(player_name, []):
            player_played[VALUES[card.value]] += 1
        
        # Simple estimate: proportional distribution
        player_remaining = self._player_remaining_counts.get(player_name, 17)
        total_remaining = sum(remaining.values())
        
        if total_remaining == 0:
            return {}
        
        proportion = player_remaining / total_remaining
        estimate = {}
        for value, count in remaining.items():
            estimate[value] = round(count * proportion)
        
        return estimate
    
    def get_current_table_description(self) -> str:
        """Get human-readable description of current table state"""
        if self.table_series.type == CardType.INVALID:
            return "桌上无牌，首家出牌"
        return f"当前牌型: {self.table_series}，由 {self.last_player_name} 打出"
    
    def get_game_progress_summary(self) -> str:
        """Get summary of game progress"""
        lines = ["=" * 40]
        lines.append(f"回合: {self.turn_count}")
        lines.append(f"当前出牌: {self.players[self.current_player_idx].name}")
        lines.append("")
        
        for p in self.players:
            role = "【地主】" if p.is_landlord else "【农民】"
            lines.append(f"{p.name}{role}: {len(p.cards)}张牌")
        
        lines.append("")
        lines.append(self.get_current_table_description())
        lines.append("=" * 40)
        
        return "\n".join(lines)
    
    def get_opponents_info(self, player_name: str) -> List[Tuple[str, int, str]]:
        """
        Get information about opponent players.
        Returns list of (name, remaining_cards, role)
        """
        info = []
        for p in self.players:
            if p.name != player_name:
                role = "地主" if p.is_landlord else "农民"
                info.append((p.name, len(p.cards), role))
        return info
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization"""
        return {
            "turn_count": self.turn_count,
            "current_player": self.players[self.current_player_idx].name,
            "landlord": self.players[self.landlord_idx].name,
            "table": str(self.table_series) if self.table_series.type != CardType.INVALID else "无",
            "players": [
                {
                    "name": p.name,
                    "role": "地主" if p.is_landlord else "农民",
                    "remaining": len(p.cards)
                }
                for p in self.players
            ]
        }


class CardTracker:
    """
    Advanced card tracking for AI memory.
    Tracks which cards are definitely held by which players.
    """
    
    def __init__(self, players: List[Player]):
        self.players = {p.name: p for p in players}
        self.known_hands: Dict[str, Set[int]] = {p.name: set() for p in players}
        self.played_by_player: Dict[str, List[Card]] = {p.name: [] for p in players}
        
        # Track definite cards (e.g., seen during play)
        self.definite_cards: Dict[str, Set[int]] = {p.name: set() for p in players}
    
    def record_play(self, player_name: str, cards: List[Card]):
        """Record cards played by a player"""
        self.played_by_player[player_name].extend(cards)
        for card in cards:
            self.known_hands[player_name].discard(card.id)
            self.definite_cards[player_name].discard(card.id)
    
    def mark_definite_card(self, player_name: str, card: Card):
        """Mark a card as definitely held by a player"""
        self.definite_cards[player_name].add(card.id)
        self.known_hands[player_name].add(card.id)
    
    def infer_from_history(self, game_state: GameState):
        """Infer card distributions from play history"""
        # Track which high cards have been played
        high_cards_played = defaultdict(set)
        
        for record in game_state.play_history:
            if not record.is_pass:
                for card in record.series.cards:
                    if card.value >= 10:  # 10, J, Q, K, A, 2, Jokers
                        high_cards_played[record.player_name].add(card.value)
        
        return dict(high_cards_played)
    
    def get_remaining_high_cards(self, game_state: GameState) -> Dict[str, List[str]]:
        """
        Get remaining high cards that are likely still in play.
        Returns dict of card value -> list of possible holders
        """
        all_high = set(range(10, 15))  # 10 through Big Joker
        played_high = set()
        
        for record in game_state.play_history:
            if not record.is_pass:
                for card in record.series.cards:
                    if card.value >= 10:
                        played_high.add(card.value)
        
        remaining = all_high - played_high
        
        # Estimate who might have them
        result = {}
        for val in remaining:
            card_name = VALUES[val]
            possible = []
            for name, player in self.players.items():
                if len(player.cards) > 0:  # Still in game
                    possible.append(name)
            result[card_name] = possible
        
        return result
