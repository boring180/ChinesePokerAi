"""
Game Runner - Main game loop for Chinese Poker AI
Replaces the notebook implementation with clean Python code
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import json
import os
from datetime import datetime

from game_control import Player, Card, Series, CardType, validate_series, deal_cards, assign_landlord, check_game_end
from game_state import GameState, CardTracker
from ai_agent import BaseAgent, NormalAgent, CoTAgent, ToolAgent, FullAgent
import API_llm as API


@dataclass
class GameResult:
    """Result of a single game"""
    winner_idx: int
    winner_name: str
    winner_role: str
    turn_count: int
    error_count: int
    players_final_cards: Dict[str, int]
    play_history: List[Dict]
    
    def to_dict(self) -> dict:
        return {
            "winner_idx": self.winner_idx,
            "winner_name": self.winner_name,
            "winner_role": self.winner_role,
            "turn_count": self.turn_count,
            "error_count": self.error_count,
            "players_final_cards": self.players_final_cards,
        }


class GameRunner:
    """
    Runs a complete game of Chinese Poker with AI agents.
    """
    
    def __init__(self, agents: List[BaseAgent], verbose: bool = True, 
                 max_retries: int = 3, enable_logging: bool = False):
        """
        Initialize game runner.
        
        Args:
            agents: List of 3 AI agents (one per player)
            verbose: Whether to print game progress
            max_retries: Max retries for invalid plays
            enable_logging: Whether to log game to file
        """
        if len(agents) != 3:
            raise ValueError("Exactly 3 agents required")
        
        self.agents = agents
        self.verbose = verbose
        self.max_retries = max_retries
        self.enable_logging = enable_logging
        self.log_file = None
        
        # Initialize players
        self.players = [
            Player("玩家一"),
            Player("玩家二"),
            Player("玩家三")
        ]
        
        # Assign agent names to match players
        for i, agent in enumerate(agents):
            agent.name = self.players[i].name
    
    def _log(self, message: str):
        """Log message if logging enabled"""
        if self.enable_logging and self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        if self.verbose:
            print(message)
    
    def run_game(self, random_landlord: bool = True, 
                 landlord_idx: int = 0) -> GameResult:
        """
        Run a single complete game.
        
        Args:
            random_landlord: Whether to randomly assign landlord
            landlord_idx: Fixed landlord index if not random
        
        Returns:
            GameResult with game statistics
        """
        # Setup logging
        if self.enable_logging:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"game_log_{timestamp}.txt"
        
        self._log("=" * 50)
        self._log("开始新游戏")
        self._log("=" * 50)
        
        # Reset players
        for p in self.players:
            p.cards = []
            p.is_landlord = False
            p.history = []
        
        # Deal cards
        landlord_cards = deal_cards(self.players)
        landlord_idx = assign_landlord(
            self.players, landlord_cards, 
            landlord_idx=landlord_idx, 
            random_assign=random_landlord
        )
        
        # Initialize game state
        game_state = GameState()
        game_state.initialize(self.players, landlord_idx)
        
        # Initialize card tracker
        card_tracker = CardTracker(self.players)
        
        # Setup agents with system prompts
        for i, agent in enumerate(self.agents):
            system_prompt = agent.get_system_prompt(self.players[i].is_landlord)
            self.players[i].add_history({"role": "system", "content": system_prompt})
            agent.history = [{"role": "system", "content": system_prompt}]
        
        # Log initial state
        game_start_msg = self._format_game_start()
        self._log(game_start_msg)
        
        # Add game state to all histories
        for p in self.players:
            p.add_history({"role": "system", "content": game_start_msg})
        
        # Game loop
        error_count = 0
        turn_count = 0
        current_idx = landlord_idx
        
        while True:
            turn_count += 1
            player = self.players[current_idx]
            agent = self.agents[current_idx]
            
            # Check if table should be cleared
            if game_state.consecutive_passes >= 2:
                game_state.clear_table()
                self._log(f"\n【回合{turn_count}】两家不要，{player.name}获得出牌权")
            else:
                self._log(f"\n【回合{turn_count}】轮到 {player.name}")
            
            # Get agent's play
            success, result = self._get_agent_play(
                agent, player, game_state, card_tracker
            )
            
            if not success:
                # Fatal error (shouldn't happen with proper retries)
                self._log(f"错误: {result}")
                error_count += 1
                # Force pass
                game_state.record_play(player.name, Series(), is_pass=True)
                game_state.pass_turn()
            elif result == "PASS":
                # Player passed
                game_state.record_play(player.name, Series(), is_pass=True)
                game_state.pass_turn()
                self._log(f"{player.name} 选择: PASS (不要)")
            else:
                # Valid play
                cards_played = result
                series = validate_series(cards_played)
                
                # Update player hand
                player.play_cards(cards_played)
                
                # Update game state
                game_state.play(player.name, series)
                card_tracker.record_play(player.name, cards_played)
                
                self._log(f"{player.name} 出牌: {series}")
                self._log(f"  剩余 {len(player.cards)} 张牌")
            
            # Check win condition
            game_ended, winner_idx = check_game_end(self.players)
            if game_ended:
                winner = self.players[winner_idx]
                winner_role = "地主" if winner.is_landlord else "农民"
                
                self._log("\n" + "=" * 50)
                self._log(f"游戏结束! {winner.name} ({winner_role}) 获胜!")
                self._log(f"总回合数: {turn_count}")
                self._log(f"错误次数: {error_count}")
                self._log("=" * 50)
                
                # Final card counts
                final_cards = {p.name: len(p.cards) for p in self.players}
                
                return GameResult(
                    winner_idx=winner_idx,
                    winner_name=winner.name,
                    winner_role=winner_role,
                    turn_count=turn_count,
                    error_count=error_count,
                    players_final_cards=final_cards,
                    play_history=[h for p in self.players for h in p.history]
                )
            
            # Next player
            current_idx = (current_idx + 1) % 3
            game_state.current_player_idx = current_idx
    
    def _get_agent_play(self, agent: BaseAgent, player: Player,
                        game_state: GameState, card_tracker: CardTracker,
                        retry_count: int = 0) -> Tuple[bool, any]:
        """
        Get play from agent with retry logic.
        
        Returns:
            (success, result) where result is either "PASS" or List[Card]
        """
        # Build prompt
        if isinstance(agent, (ToolAgent, FullAgent)):
            prompt = agent.build_prompt(player, game_state, card_tracker)
        else:
            prompt = agent.build_prompt(player, game_state)
        
        # Get response from LLM
        try:
            response = API.get_llm_reaction(agent.history, prompt)
        except Exception as e:
            if retry_count < self.max_retries:
                return self._get_agent_play(
                    agent, player, game_state, card_tracker, retry_count + 1
                )
            return False, f"LLM API error: {str(e)}"
        
        # Parse response
        if isinstance(agent, (ToolAgent, FullAgent)):
            is_pass, full_response, cards_or_tool, is_tool = agent.parse_response(response)
            
            if is_tool:
                # Execute tool and get follow-up
                tool_result = agent.execute_tool_call(
                    cards_or_tool[0], player, game_state, card_tracker
                )
                
                # Add tool result to prompt and get new response
                follow_up_prompt = prompt + f"\n\n【工具结果】\n{tool_result}\n\n基于以上信息，请给出你的出牌决策:"
                
                try:
                    follow_up_response = API.get_llm_reaction(agent.history, follow_up_prompt)
                    response = follow_up_response
                    # Re-parse as regular response
                    is_pass, full_response, cards_or_tool, is_tool = agent.parse_response(response)
                    if is_tool:
                        # If still calling tool, just use valid moves
                        cards_or_tool = []
                        is_pass = False
                    cards = cards_or_tool
                except Exception as e:
                    if retry_count < self.max_retries:
                        return self._get_agent_play(
                            agent, player, game_state, card_tracker, retry_count + 1
                        )
                    return False, str(e)
            else:
                cards = cards_or_tool
        else:
            is_pass, full_response, cards = agent.parse_response(response)
        
        # Update agent history
        agent.add_to_history("user", prompt)
        agent.add_to_history("assistant", response)
        player.add_history({"role": "assistant", "content": response})
        
        # Handle PASS
        if is_pass:
            # Check if PASS is valid (not first player or after clear)
            if game_state.table_series.type == CardType.INVALID:
                # Can't pass as first player
                error_msg = "你是首家，不能PASS，必须出牌"
                if retry_count < self.max_retries:
                    return self._get_agent_play_with_error(
                        agent, player, game_state, card_tracker, error_msg, retry_count
                    )
                # Force minimum play
                if player.cards:
                    return True, [player.cards[0]]
                return False, "No cards to play"
            return True, "PASS"
        
        # Validate card selection
        if not cards:
            error_msg = "未能识别出牌"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_error(
                    agent, player, game_state, card_tracker, error_msg, retry_count
                )
            return False, "Invalid card selection"
        
        # Check if player has these cards
        selected_cards = player.has_cards(cards)
        if not selected_cards or len(selected_cards) != len(cards):
            error_msg = f"手牌中没有这些牌: {cards}"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_error(
                    agent, player, game_state, card_tracker, error_msg, retry_count
                )
            return False, error_msg
        
        # Validate series
        series = validate_series(selected_cards)
        if series.type == CardType.INVALID:
            error_msg = f"牌型无效: {cards}"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_error(
                    agent, player, game_state, card_tracker, error_msg, retry_count
                )
            return False, error_msg
        
        # Check if can beat table
        if game_state.table_series.type != CardType.INVALID:
            can_beat, reason = series.can_beat(game_state.table_series)
            if not can_beat:
                error_msg = f"无法压过桌上的牌: {reason}"
                if retry_count < self.max_retries:
                    return self._get_agent_play_with_error(
                        agent, player, game_state, card_tracker, error_msg, retry_count
                    )
                return False, error_msg
        
        # Valid play
        return True, selected_cards
    
    def _get_agent_play_with_error(self, agent: BaseAgent, player: Player,
                                    game_state: GameState, card_tracker: CardTracker,
                                    error_msg: str, retry_count: int) -> Tuple[bool, any]:
        """Retry play with error message"""
        # Build error prompt
        if isinstance(agent, (ToolAgent, FullAgent)):
            prompt = agent.build_prompt(player, game_state, card_tracker, 
                                        is_retry=True, error_msg=error_msg)
        else:
            prompt = agent.build_prompt(player, game_state, 
                                        is_retry=True, error_msg=error_msg)
        
        try:
            response = API.get_llm_reaction(agent.history, prompt)
        except Exception as e:
            if retry_count + 1 < self.max_retries:
                return self._get_agent_play(
                    agent, player, game_state, card_tracker, retry_count + 1
                )
            return False, str(e)
        
        # Update history
        agent.add_to_history("user", prompt)
        agent.add_to_history("assistant", response)
        player.add_history({"role": "assistant", "content": response})
        
        # Parse and validate
        if isinstance(agent, (ToolAgent, FullAgent)):
            is_pass, _, cards_or_tool, is_tool = agent.parse_response(response)
            if is_tool:
                # Execute tool
                tool_result = agent.execute_tool_call(
                    cards_or_tool[0], player, game_state, card_tracker
                )
                # Get new response with tool result
                follow_up_prompt = prompt + f"\n\n【工具结果】\n{tool_result}\n\n请给出最终出牌:"
                try:
                    follow_up_response = API.get_llm_reaction(agent.history, follow_up_prompt)
                    response = follow_up_response
                    is_pass, _, cards, _ = agent.parse_response(response)
                except Exception as e:
                    return False, str(e)
            else:
                cards = cards_or_tool
        else:
            is_pass, _, cards = agent.parse_response(response)
        
        if is_pass:
            if game_state.table_series.type == CardType.INVALID:
                if retry_count + 1 < self.max_retries:
                    return self._get_agent_play(
                        agent, player, game_state, card_tracker, retry_count + 1
                    )
                if player.cards:
                    return True, [player.cards[0]]
                return False, "No cards"
            return True, "PASS"
        
        if not cards:
            if retry_count + 1 < self.max_retries:
                return self._get_agent_play(
                    agent, player, game_state, card_tracker, retry_count + 1
                )
            return False, "No cards parsed"
        
        selected_cards = player.has_cards(cards)
        if not selected_cards:
            if retry_count + 1 < self.max_retries:
                return self._get_agent_play(
                    agent, player, game_state, card_tracker, retry_count + 1
                )
            return False, "Cards not in hand"
        
        series = validate_series(selected_cards)
        if series.type == CardType.INVALID:
            if retry_count + 1 < self.max_retries:
                return self._get_agent_play(
                    agent, player, game_state, card_tracker, retry_count + 1
                )
            return False, "Invalid series"
        
        if game_state.table_series.type != CardType.INVALID:
            can_beat, _ = series.can_beat(game_state.table_series)
            if not can_beat:
                if retry_count + 1 < self.max_retries:
                    return self._get_agent_play(
                        agent, player, game_state, card_tracker, retry_count + 1
                    )
                return False, "Cannot beat table"
        
        return True, selected_cards
    
    def _format_game_start(self) -> str:
        """Format game start message"""
        lines = ["游戏开始!"]
        for p in self.players:
            role = "【地主】" if p.is_landlord else "【农民】"
            lines.append(f"{p.name}{role}: {len(p.cards)}张牌")
        return "\n".join(lines)


def run_single_game(agents: List[BaseAgent], random_landlord: bool = True,
                    verbose: bool = True) -> GameResult:
    """
    Convenience function to run a single game.
    
    Args:
        agents: List of 3 agents
        random_landlord: Whether to randomize landlord
        verbose: Print game progress
    
    Returns:
        GameResult
    """
    runner = GameRunner(agents, verbose=verbose)
    return runner.run_game(random_landlord=random_landlord)


def run_multiple_games(agents: List[BaseAgent], num_games: int = 10,
                       random_landlord: bool = True, verbose: bool = False) -> List[GameResult]:
    """
    Run multiple games and collect results.
    
    Args:
        agents: List of 3 agents
        num_games: Number of games to run
        random_landlord: Whether to randomize landlord each game
        verbose: Print game progress (usually False for batch runs)
    
    Returns:
        List of GameResult
    """
    results = []
    
    for i in range(num_games):
        if verbose or i % 10 == 0:
            print(f"Running game {i+1}/{num_games}...")
        
        # Reset agents between games
        for agent in agents:
            if hasattr(agent, 'reset_tools'):
                agent.reset_tools()
            agent.history = []
        
        runner = GameRunner(agents, verbose=False)
        result = runner.run_game(random_landlord=random_landlord)
        results.append(result)
    
    return results
