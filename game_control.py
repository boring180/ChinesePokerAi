"""
Chinese Poker (Dou Di Zhu) Game Engine
Simplified and refactored for AI research
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class CardType(Enum):
    """Card types/series in Chinese Poker"""
    INVALID = "违规"
    SINGLE = "单牌"
    PAIR = "对子"
    TRIPLE = "三张"
    TRIPLE_WITH_SINGLE = "三带一"
    TRIPLE_WITH_PAIR = "三带二"
    STRAIGHT = "顺子"
    STRAIGHT_PAIRS = "连对"
    AIRPLANE = "飞机"
    BOMB = "炸弹"
    ROCKET = "王炸"
    FOUR_WITH_TWO = "四带二"


# Constants
SUITS = ['♠', '♥', '♣', '♦', '']
VALUES = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '小王', '大王']


def get_card_value_order(value: str) -> int:
    """Get the numeric order of a card value for comparison"""
    return VALUES.index(value)


@dataclass
class Card:
    """Represents a playing card"""
    suit: int  # 0-3 for ♠♥♣♦, 4 for jokers
    value: int  # 0-14 corresponding to VALUES
    
    def __post_init__(self):
        self.id = 4 * self.value + self.suit if self.suit < 4 else 52 + (self.value - 13)
    
    def __str__(self):
        return SUITS[self.suit] + VALUES[self.value]
    
    def __repr__(self):
        return f"Card({SUITS[self.suit]}{VALUES[self.value]})"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.value == other.value and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.suit, self.value))


@dataclass
class Series:
    """Represents a card series/play"""
    cards: List[Card] = field(default_factory=list)
    type: CardType = CardType.INVALID
    value: int = 0  # Main value for comparison
    length: int = 0  # For straights, consecutive pairs, airplanes
    kicker_count: int = 0  # For triples with kickers
    
    def __str__(self):
        cards_str = ''.join(str(c) for c in self.cards)
        return f"{self.type.value}: {cards_str}"
    
    def can_beat(self, other: 'Series') -> Tuple[bool, str]:
        """
        Check if this series can beat another series.
        Returns (can_beat, reason)
        """
        if self.type == CardType.INVALID:
            return False, "无效牌型"
        
        if other.type == CardType.INVALID:
            return True, "首家出牌"
        
        # Rocket beats everything
        if self.type == CardType.ROCKET:
            return True, "王炸最大"
        
        if other.type == CardType.ROCKET:
            return False, "对方王炸"
        
        # Bomb beats non-bombs
        if self.type == CardType.BOMB and other.type != CardType.BOMB:
            return True, "炸弹压制"
        
        if self.type != CardType.BOMB and other.type == CardType.BOMB:
            return False, "对方炸弹"
        
        # Same type comparison
        if self.type != other.type:
            return False, "牌型不同"
        
        if self.length != other.length:
            return False, "长度不同"
        
        if self.kicker_count != other.kicker_count:
            return False, "带牌数量不同"
        
        if self.value > other.value:
            return True, "牌值更大"
        
        return False, "牌值不够大"


def validate_series(cards: List[Card]) -> Series:
    """
    Validate a series of cards and determine its type.
    """
    if not cards:
        return Series(cards=cards, type=CardType.INVALID)
    
    n = len(cards)
    values = sorted([c.value for c in cards])
    
    # Single card
    if n == 1:
        return Series(cards=cards, type=CardType.SINGLE, value=values[0])
    
    # Pair or Rocket
    if n == 2:
        if values[0] == values[1]:
            return Series(cards=cards, type=CardType.PAIR, value=values[0])
        if values == [13, 14]:  # Small + Big Joker
            return Series(cards=cards, type=CardType.ROCKET, value=15)
        return Series(cards=cards, type=CardType.INVALID)
    
    # Three cards
    if n == 3:
        if values[0] == values[1] == values[2]:
            return Series(cards=cards, type=CardType.TRIPLE, value=values[0])
        return Series(cards=cards, type=CardType.INVALID)
    
    # Four cards
    if n == 4:
        # Bomb
        if len(set(values)) == 1:
            return Series(cards=cards, type=CardType.BOMB, value=values[0])
        # Triple with single
        if (values[0] == values[1] == values[2] != values[3] or
            values[1] == values[2] == values[3] != values[0]):
            main_value = values[1]  # Middle value is the triple
            return Series(cards=cards, type=CardType.TRIPLE_WITH_SINGLE, 
                         value=main_value, kicker_count=1)
        return Series(cards=cards, type=CardType.INVALID)
    
    # Five cards
    if n == 5:
        # Triple with pair
        if (values[0] == values[1] == values[2] and values[3] == values[4] and values[2] != values[3]):
            return Series(cards=cards, type=CardType.TRIPLE_WITH_PAIR, 
                         value=values[0], kicker_count=2)
        if (values[0] == values[1] and values[2] == values[3] == values[4] and values[1] != values[2]):
            return Series(cards=cards, type=CardType.TRIPLE_WITH_PAIR, 
                         value=values[2], kicker_count=2)
        # Straight
        if is_straight(values):
            return Series(cards=cards, type=CardType.STRAIGHT, 
                         value=values[-1], length=n)
        return Series(cards=cards, type=CardType.INVALID)
    
    # Six cards
    if n == 6:
        # Airplane (two consecutive triples)
        if (values[0] == values[1] == values[2] and 
            values[3] == values[4] == values[5] and 
            values[2] + 1 == values[3] and values[5] < 12):  # Not ending with 2
            return Series(cards=cards, type=CardType.AIRPLANE, 
                         value=values[3], length=2)
        # Four with two singles
        # Count occurrences
        from collections import Counter
        counts = Counter(values)
        if 4 in counts.values() and len(counts) == 3:
            four_val = [k for k, v in counts.items() if v == 4][0]
            return Series(cards=cards, type=CardType.FOUR_WITH_TWO, 
                         value=four_val, kicker_count=2)
        # Straight
        if is_straight(values):
            return Series(cards=cards, type=CardType.STRAIGHT, 
                         value=values[-1], length=n)
        # Straight pairs (3 pairs)
        if is_straight_pairs(values):
            return Series(cards=cards, type=CardType.STRAIGHT_PAIRS, 
                         value=values[-1], length=3)
        return Series(cards=cards, type=CardType.INVALID)
    
    # More than 6 cards
    if n > 6:
        # Straights (5+)
        if n >= 5 and is_straight(values):
            return Series(cards=cards, type=CardType.STRAIGHT, 
                         value=values[-1], length=n)
        # Straight pairs (6+, even)
        if n >= 6 and n % 2 == 0 and is_straight_pairs(values):
            return Series(cards=cards, type=CardType.STRAIGHT_PAIRS, 
                         value=values[-1], length=n // 2)
        # Airplane with wings
        # Simplified: check for consecutive triples pattern
        airplane = detect_airplane(values, n)
        if airplane:
            return airplane
    
    return Series(cards=cards, type=CardType.INVALID)


def is_straight(values: List[int]) -> bool:
    """Check if values form a valid straight (5+ consecutive, not including 2 or jokers)"""
    if len(values) < 5:
        return False
    if values[-1] >= 12:  # Ends with 2 or joker - invalid
        return False
    return all(values[i] + 1 == values[i + 1] for i in range(len(values) - 1))


def is_straight_pairs(values: List[int]) -> bool:
    """Check if values form valid consecutive pairs (3+ pairs)"""
    if len(values) < 6 or len(values) % 2 != 0:
        return False
    if values[-1] >= 12:  # Ends with 2 - invalid
        return False
    # Check pairs
    for i in range(0, len(values), 2):
        if values[i] != values[i + 1]:
            return False
    # Check consecutive
    pair_values = [values[i] for i in range(0, len(values), 2)]
    return all(pair_values[i] + 1 == pair_values[i + 1] for i in range(len(pair_values) - 1))


def detect_airplane(values: List[int], n: int) -> Optional[Series]:
    """
    Detect airplane pattern (consecutive triples with optional wings).
    Returns Series if valid airplane, None otherwise.
    """
    from collections import Counter
    counts = Counter(values)
    
    # Find triples
    triples = sorted([v for v, c in counts.items() if c >= 3 and v < 12])  # Exclude 2 and jokers
    
    if len(triples) < 2:
        return None
    
    # Find longest consecutive triples sequence
    best_start = 0
    best_len = 1
    current_start = 0
    current_len = 1
    
    for i in range(1, len(triples)):
        if triples[i] == triples[i - 1] + 1:
            current_len += 1
        else:
            if current_len > best_len:
                best_len = current_len
                best_start = current_start
            current_start = i
            current_len = 1
    
    if current_len > best_len:
        best_len = current_len
        best_start = current_start
    
    if best_len < 2:
        return None
    
    # Get the consecutive triples
    seq_triples = triples[best_start:best_start + best_len]
    triple_cards_count = best_len * 3
    
    # Check remaining cards (wings)
    remaining = n - triple_cards_count
    if remaining > best_len * 2:  # Can't have more than 2 cards per triple as wings
        return None
    
    # Verify the wings exist
    used = []
    for v in seq_triples:
        used.extend([v] * 3)
    
    wings = [v for v in values if v not in used or used.remove(v) is None]
    # Simple validation: wings should exist
    
    return Series(
        cards=[],  # Will be populated by caller
        type=CardType.AIRPLANE,
        value=seq_triples[-1],
        length=best_len,
        kicker_count=remaining
    )


class Player:
    """Represents a game player"""
    
    def __init__(self, name: str):
        self.name = name
        self.cards: List[Card] = []
        self.is_landlord = False
        self.history: List[dict] = []
    
    def assign_cards(self, cards: List[Card]):
        """Assign cards to player, sorted by value"""
        self.cards = sorted(cards, key=lambda c: c.value * 4 + c.suit)
    
    def become_landlord(self, extra_cards: List[Card]):
        """Make player landlord with extra cards"""
        self.is_landlord = True
        self.cards.extend(extra_cards)
        self.cards = sorted(self.cards, key=lambda c: c.value * 4 + c.suit)
    
    def get_cards_string(self) -> str:
        """Get string representation of hand"""
        return ''.join(str(c) for c in self.cards)
    
    def play_cards(self, cards: List[Card]) -> bool:
        """Remove cards from hand after playing"""
        for card in cards:
            if card not in self.cards:
                return False
        for card in cards:
            self.cards.remove(card)
        return True
    
    def has_cards(self, card_strs: List[str]) -> List[Card]:
        """Check if player has specific cards by string representation"""
        result = []
        remaining = self.cards[:]
        for s in card_strs:
            found = False
            for card in remaining:
                if str(card) == s and not found:
                    result.append(card)
                    remaining.remove(card)
                    found = True
        return result if len(result) == len(card_strs) else []
    
    def is_winner(self) -> bool:
        """Check if player has won (no cards left)"""
        return len(self.cards) == 0
    
    def add_history(self, entry: dict):
        """Add to conversation history"""
        self.history.append(entry)
    
    def get_history(self) -> List[dict]:
        """Get conversation history"""
        return self.history
    
    def __str__(self):
        landlord_status = "是" if self.is_landlord else "不是"
        return f"{self.name}，有{len(self.cards)}张手牌，{landlord_status}地主。"


class GameTable:
    """Represents the current play on the table"""
    
    def __init__(self):
        self.current_series: Series = Series()
        self.last_player: Optional[str] = None
        self.pass_count = 0
    
    def clear(self):
        """Clear the table (new round)"""
        self.current_series = Series()
        self.last_player = None
        self.pass_count = 0
    
    def play(self, player_name: str, series: Series):
        """Play a series on the table"""
        self.current_series = series
        self.last_player = player_name
        self.pass_count = 0
    
    def pass_turn(self):
        """Player passes"""
        self.pass_count += 1
    
    def should_clear(self) -> bool:
        """Check if table should be cleared (2 consecutive passes)"""
        return self.pass_count >= 2


def create_deck() -> List[Card]:
    """Create and return a shuffled deck"""
    deck = [Card(suit, value) for suit in range(4) for value in range(13)]
    deck.append(Card(4, 13))  # Small joker
    deck.append(Card(4, 14))  # Big joker
    random.shuffle(deck)
    return deck


def deal_cards(players: List[Player]) -> List[Card]:
    """Deal cards to players, return landlord cards"""
    deck = create_deck()
    players[0].assign_cards(deck[0:17])
    players[1].assign_cards(deck[17:34])
    players[2].assign_cards(deck[34:51])
    return deck[51:54]


def assign_landlord(players: List[Player], landlord_cards: List[Card], 
                   landlord_idx: int = 0, random_assign: bool = False) -> int:
    """Assign landlord role to a player"""
    if random_assign:
        landlord_idx = random.randrange(3)
    players[landlord_idx].become_landlord(landlord_cards)
    return landlord_idx


def check_game_end(players: List[Player]) -> Tuple[bool, int]:
    """Check if game has ended, return (ended, winner_idx)"""
    for i, player in enumerate(players):
        if player.is_winner():
            return True, i
    return False, -1


def get_game_state_message(players: List[Player], landlord_cards: List[Card]) -> str:
    """Get game start state message"""
    landlord_info = f"地主牌：{landlord_cards[0]}{landlord_cards[1]}{landlord_cards[2]}"
    return f"{players[0]}\n{players[1]}\n{players[2]}\n{landlord_info}"


# Legacy compatibility functions
def gameStart(players):
    """Legacy function for game start"""
    return deal_cards(players)


def landlordDecide(players, landLordCards, landLordNumber=0, rand=True):
    """Legacy function for landlord decision"""
    idx = assign_landlord(players, landLordCards, landLordNumber, rand)
    return idx, get_game_state_message(players, landLordCards)


def gameEnd(players):
    """Legacy function for game end check"""
    return check_game_end(players)


def seriesValidate(cards):
    """Legacy function for series validation"""
    return validate_series(cards)
