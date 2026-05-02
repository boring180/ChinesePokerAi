"""
Game Runner - Main game loop for Chinese Poker AI
True Tool-Calling implementation
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import json
import os
from datetime import datetime

from game_control import Player, Card, Series, CardType, validate_series, deal_cards, assign_landlord, check_game_end
from game_state import GameState, CardTracker
from ai_agent import BaseAgent, NormalAgent, CoTAgent, ToolAgent, FullAgent, GuideAgent, ToolCall
from tools import (
    CardHistoryTool, ValidMovesTool, TreeSearchTool
)
import API_llm as API


@dataclass
class GameResult:
    """Result of a single game"""
    winner_idx: int  # First winner (the one who emptied hand)
    winner_name: str
    winner_role: str
    winner_indices: List[int]  # All winners (1 for landlord, 2 for farmers)
    winner_names: List[str]    # All winner names
    turn_count: int
    error_count: int
    players_final_cards: Dict[str, int]
    play_history: List[Dict]
    tool_call_counts: Dict[str, int]  # Tool name -> count

    def to_dict(self) -> dict:
        return {
            "winner_idx": self.winner_idx,
            "winner_name": self.winner_name,
            "winner_role": self.winner_role,
            "winner_indices": self.winner_indices,
            "winner_names": self.winner_names,
            "turn_count": self.turn_count,
            "error_count": self.error_count,
            "players_final_cards": self.players_final_cards,
            "tool_call_counts": self.tool_call_counts,
        }


class GameRunner:
    """
    Runs a complete game of Chinese Poker with AI agents.
    Supports true tool calling with two-phase flow.
    """
    
    def __init__(self, agents: List[BaseAgent], verbose: bool = True, 
                 max_retries: int = 3, enable_logging: bool = False,
                 log_folder: str = "logs", experiment_name: str = None):
        """
        Initialize game runner.
        
        Args:
            agents: List of 3 AI agents (one per player)
            verbose: Whether to print game progress
            max_retries: Max retries for invalid plays
            enable_logging: Whether to log game to file
            log_folder: Folder to save logs (default: "logs")
            experiment_name: Name of experiment for subfolder
        """
        if len(agents) != 3:
            raise ValueError("Exactly 3 agents required")
        
        self.agents = agents
        self.verbose = verbose
        self.max_retries = max_retries
        self.enable_logging = enable_logging
        self.log_file = None
        self.log_folder = log_folder
        
        # Create log folder structure
        if self.enable_logging:
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
            
            if experiment_name:
                self.log_folder = os.path.join(log_folder, experiment_name)
                if not os.path.exists(self.log_folder):
                    os.makedirs(self.log_folder)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_folder = os.path.join(self.log_folder, timestamp)
            os.makedirs(self.log_folder)
        
        # Initialize players
        self.players = [
            Player("玩家一"),
            Player("玩家二"),
            Player("玩家三")
        ]
        
        # Assign agent names to match players
        for i, agent in enumerate(agents):
            agent.name = self.players[i].name

        # Tool call tracking
        self.tool_call_counts: Dict[str, int] = {}

    def _track_tool_call(self, tool_name: str):
        """Track a tool call"""
        if tool_name:
            self.tool_call_counts[tool_name] = self.tool_call_counts.get(tool_name, 0) + 1

    def _get_tool_call_summary(self) -> str:
        """Get a formatted summary of tool calls"""
        if not self.tool_call_counts:
            return "无工具调用"

        lines = ["工具调用统计:"]
        total = sum(self.tool_call_counts.values())
        lines.append(f"  总计: {total} 次")
        lines.append("")

        # Sort by count descending
        sorted_tools = sorted(self.tool_call_counts.items(), key=lambda x: x[1], reverse=True)
        for tool_name, count in sorted_tools:
            percentage = (count / total) * 100 if total > 0 else 0
            lines.append(f"  {tool_name}: {count} 次 ({percentage:.1f}%)")

        return "\n".join(lines)

    def _log(self, message: str):
        """Log message if logging enabled"""
        if self.enable_logging and self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        if self.verbose:
            print(message)
    
    def _log_llm_interaction(self, player_name: str, prompt: str, response: str, 
                               is_error: bool = False, error_msg: str = None,
                               tool_call: ToolCall = None, tool_result: str = None):
        """Log LLM interaction to a separate file for debugging"""
        if not self.enable_logging:
            return
        
        llm_log_file = os.path.join(self.log_folder, "llm_interactions.txt")
        
        with open(llm_log_file, 'a', encoding='utf-8') as f:
            f.write("=" * 60 + '\n')
            f.write(f"Player: {player_name} | Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}\n")
            if tool_call:
                f.write(f"Status: TOOL_CALL - {tool_call.tool_name}\n")
            elif is_error and error_msg:
                f.write(f"Status: ERROR - {error_msg}\n")
            else:
                f.write(f"Status: SUCCESS\n")
            f.write("-" * 60 + '\n')
            f.write("PROMPT:\n")
            f.write(prompt + '\n')
            f.write("-" * 60 + '\n')
            f.write("RESPONSE:\n")
            f.write(response if response else "[No response - Error]")
            f.write('\n')
            if tool_result:
                f.write("-" * 60 + '\n')
                f.write("TOOL_RESULT:\n")
                f.write(tool_result + '\n')
            f.write('\n')
    
    def _save_detailed_history(self, game_id: str):
        """Save detailed player histories to separate files"""
        if not self.enable_logging:
            return
        
        for i, player in enumerate(self.players):
            history_file = os.path.join(self.log_folder, f"game_{game_id}_player{i+1}_{player.name}.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "player_name": player.name,
                    "role": "landlord" if player.is_landlord else "farmer",
                    "final_card_count": len(player.cards),
                    "conversation_history": player.history
                }, f, ensure_ascii=False, indent=2)
    
    def _save_summary(self, result: GameResult, game_id: str):
        """Save game summary to JSON file"""
        if not self.enable_logging:
            return
        
        summary_data = {
            "game_id": game_id,
            "winners": {
                "primary": {
                    "name": result.winner_name,
                    "role": result.winner_role,
                    "index": result.winner_idx
                },
                "all": [
                    {"name": name, "index": idx}
                    for name, idx in zip(result.winner_names, result.winner_indices)
                ]
            },
            "statistics": {
                "turn_count": result.turn_count,
                "error_count": result.error_count,
                "error_rate": result.error_count / max(1, result.turn_count)
            },
            "tool_statistics": {
                "total_calls": sum(result.tool_call_counts.values()),
                "calls_by_tool": result.tool_call_counts
            },
            "final_state": {
                player_name: card_count
                for player_name, card_count in result.players_final_cards.items()
            },
            "players": [
                {
                    "name": player.name,
                    "role": "landlord" if player.is_landlord else "farmer",
                    "agent_type": self.agents[i].__class__.__name__,
                    "final_cards": len(player.cards)
                }
                for i, player in enumerate(self.players)
            ]
        }
        
        summary_file = os.path.join(self.log_folder, f"game_{game_id}_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
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
        game_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        if self.enable_logging:
            self.log_file = os.path.join(self.log_folder, f"game_{game_id}.txt")
        
        self._log("=" * 50)
        self._log("开始新游戏")
        self._log("=" * 50)
        self._log(f"Game ID: {game_id}")
        self._log(f"Log folder: {self.log_folder if self.enable_logging else 'N/A'}")
        
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
            
            # Get agent's play (handles tool calling internally)
            success, result, turn_errors, attempted_play = self._get_agent_play_with_tools(
                agent, player, game_state, card_tracker
            )

            # Accumulate errors from this turn (including retries)
            error_count += turn_errors

            if not success:
                # Fatal error - show the attempted play
                error_detail = f" (尝试出: {attempted_play})" if attempted_play else ""
                self._log(f"❌ 错误: {result}{error_detail}")
                game_state.record_play(player.name, Series(), is_pass=True)
            elif result == "PASS":
                game_state.record_play(player.name, Series(), is_pass=True)
                self._log(f"{player.name} 选择: PASS (不要)")
            else:
                # Valid play
                cards_played = result
                series = validate_series(cards_played)
                
                # Update player hand
                player.play_cards(cards_played)
                
                # Update game state
                game_state.record_play(player.name, series, is_pass=False)
                card_tracker.record_play(player.name, cards_played)
                
                self._log(f"{player.name} 出牌: {series}")
                self._log(f"  剩余 {len(player.cards)} 张牌")
            
            # Check win condition
            game_ended, winner_idx = check_game_end(self.players)
            if game_ended:
                winner = self.players[winner_idx]
                winner_role = "地主" if winner.is_landlord else "农民"
                winner_agent_type = self.agents[winner_idx].__class__.__name__

                # Determine all winners
                if winner.is_landlord:
                    # Landlord wins alone
                    winner_indices = [winner_idx]
                    winner_names = [winner.name]
                    winner_display = f"{winner.name} (地主)"
                else:
                    # Farmer wins - both farmers win
                    winner_indices = []
                    winner_names = []
                    farmer_names = []
                    for i, p in enumerate(self.players):
                        if not p.is_landlord:
                            winner_indices.append(i)
                            winner_names.append(p.name)
                            agent_type = self.agents[i].__class__.__name__
                            farmer_names.append(f"{p.name} ({agent_type})")
                    winner_display = " | ".join(farmer_names)

                self._log("\n" + "=" * 50)
                if winner.is_landlord:
                    self._log(f"游戏结束! {winner.name} (地主) 获胜!")
                    self._log(f"胜者类型: {winner_agent_type}")
                else:
                    self._log(f"游戏结束! 农民获胜!")
                    self._log(f"获胜农民: {', '.join(winner_names)}")
                self._log(f"总回合数: {turn_count}")
                self._log(f"错误次数: {error_count}")
                self._log("=" * 50)

                # Print game completion message
                print(f"\n✓ Game completed!")
                if winner.is_landlord:
                    print(f"  Winner: {winner.name} (地主) - {winner_agent_type}")
                else:
                    print(f"  Winners (Farmers): {winner_display}")
                print(f"  Turns: {turn_count}, Errors: {error_count}")

                # Display tool call summary
                tool_summary = self._get_tool_call_summary()
                print(f"\n  {tool_summary.replace(chr(10), chr(10) + '  ')}")
                self._log("\n" + tool_summary)

                # Final card counts
                final_cards = {p.name: len(p.cards) for p in self.players}

                # Create result
                result = GameResult(
                    winner_idx=winner_idx,
                    winner_name=winner.name,
                    winner_role=winner_role,
                    winner_indices=winner_indices,
                    winner_names=winner_names,
                    turn_count=turn_count,
                    error_count=error_count,
                    players_final_cards=final_cards,
                    play_history=[h for p in self.players for h in p.history],
                    tool_call_counts=self.tool_call_counts.copy()
                )
                
                # Save detailed logs if enabled
                if self.enable_logging:
                    self._save_detailed_history(game_id)
                    self._save_summary(result, game_id)
                
                return result
            
            # Next player
            current_idx = (current_idx + 1) % 3
            game_state.current_player_idx = current_idx
    
    def _get_agent_play_with_tools(self, agent: BaseAgent, player: Player,
                                    game_state: GameState, card_tracker: CardTracker,
                                    retry_count: int = 0, accumulated_errors: int = 0,
                                    phase: str = "initial", tool_result: str = None,
                                    error_msg: str = None) -> Tuple[bool, any, int]:
        """
        Get play from agent with tool calling support.
        
        Two-phase flow:
        1. Phase "initial": Agent can call a tool OR play cards
        2. Phase "after_tool": Agent sees tool result, MUST play cards (no more tools)
        
        Returns:
            (success, result, error_count) where result is "PASS" or List[Card]
        """
        is_tool_agent = isinstance(agent, (ToolAgent, FullAgent))
        
        # Build appropriate prompt
        if is_tool_agent:
            prompt = agent.build_prompt(
                player, game_state, card_tracker,
                phase=phase,
                tool_result=tool_result,
                is_retry=(retry_count > 0 and not tool_result),
                error_msg=error_msg if error_msg else ""
            )
        else:
            prompt = agent.build_prompt(
                player, game_state,
                is_retry=(retry_count > 0),
                error_msg=error_msg if error_msg else ""
            )
        
        # Get response from LLM
        try:
            response = API.get_llm_reaction(agent.history, prompt)
            self._log_llm_interaction(
                player.name, prompt, response,
                is_error=False
            )
        except Exception as e:
            accumulated_errors += 1
            error_msg = f"API Error: {str(e)}"
            self._log_llm_interaction(
                player.name, prompt, "",
                is_error=True, error_msg=error_msg
            )
            if retry_count < self.max_retries:
                return self._get_agent_play_with_tools(
                    agent, player, game_state, card_tracker,
                    retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                    phase=phase, tool_result=tool_result, error_msg=error_msg
                )
            return False, f"LLM API error: {str(e)}", accumulated_errors, ""

        # Parse response
        is_pass, full_response, cards, tool_call = agent.parse_response(response)
        
        # Update agent history
        agent.add_to_history("user", prompt)
        agent.add_to_history("assistant", response)
        player.add_history({"role": "assistant", "content": response})
        
        # Handle tool calling (only in phase "initial")
        if is_tool_agent and phase == "initial" and tool_call:
            # Track the tool call
            self._track_tool_call(tool_call.tool_name)

            # Execute the tool
            try:
                tool_result_str = self._execute_tool_for_agent(
                    tool_call.tool_name, player, game_state, card_tracker
                )
            except Exception as e:
                tool_result_str = f"[工具执行错误: {str(e)}]"

            # Log the tool interaction
            self._log_llm_interaction(
                player.name, prompt, response,
                tool_call=tool_call, tool_result=tool_result_str
            )

            self._log(f"{player.name} 调用工具: {tool_call.tool_name}")
            
            # Transition to phase "after_tool" - agent must now play cards
            return self._get_agent_play_with_tools(
                agent, player, game_state, card_tracker,
                retry_count=0,  # Reset retries for the actual decision
                accumulated_errors=accumulated_errors,
                phase="after_tool",
                tool_result=tool_result_str,
                error_msg=error_msg
            )
        
        # If agent tries to call a tool in "after_tool" phase, that's an error
        if is_tool_agent and phase == "after_tool" and tool_call:
            accumulated_errors += 1
            error_msg = "工具结果已提供，请直接出牌，不要再调用工具"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_tools(
                    agent, player, game_state, card_tracker,
                    retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                    phase="after_tool",  # Stay in after_tool phase
                    tool_result=tool_result, error_msg=error_msg
                )
            # Force a pass after max retries
            return True, "PASS", accumulated_errors, ""
        
        # Handle PASS
        if is_pass:
            if game_state.table_series.type == CardType.INVALID:
                accumulated_errors += 1
                error_msg = "你是首家，不能PASS，必须出牌"
                if retry_count < self.max_retries:
                    return self._get_agent_play_with_tools(
                        agent, player, game_state, card_tracker,
                        retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                        phase=phase, tool_result=tool_result, error_msg=error_msg
                    )
                if player.cards:
                    return True, [player.cards[0]], accumulated_errors, ""
                return False, "No cards to play", accumulated_errors, ""
            return True, "PASS", accumulated_errors, ""
        
        # Validate card selection
        if not cards:
            accumulated_errors += 1
            attempted = full_response[:50] if full_response else "(无响应)"
            error_msg = f"❌ 出牌识别失败。你尝试出: '{attempted}'\n请使用正确格式: 回答: ♠3♣3\n你的手牌: {player.get_cards_string()}"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_tools(
                    agent, player, game_state, card_tracker,
                    retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                    phase=phase, tool_result=tool_result, error_msg=error_msg
                )
            return False, "Invalid card selection", accumulated_errors, full_response[:50]

        # Check if player has these cards
        selected_cards = player.has_cards(cards)
        if not selected_cards or len(selected_cards) != len(cards):
            accumulated_errors += 1
            attempted = "".join(cards)
            missing = [c for c in cards if c not in [str(card) for card in player.cards]]
            error_msg = f"❌ 手牌中没有这些牌: {missing}\n你尝试出: {attempted}\n你的手牌: {player.get_cards_string()}\n请重新选择你实际拥有的牌。"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_tools(
                    agent, player, game_state, card_tracker,
                    retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                    phase=phase, tool_result=tool_result, error_msg=error_msg
                )
            return False, "Cards not in hand", accumulated_errors, "".join(cards)

        # Validate series
        series = validate_series(selected_cards)
        if series.type == CardType.INVALID:
            accumulated_errors += 1
            attempted = "".join(cards)
            error_msg = f"❌ 牌型无效: {attempted}\n有效牌型: 单牌(♠3)、对子(♠3♥3)、三张(♠3♥3♣3)、顺子(5+连续单牌)、炸弹(4张相同)\n你的手牌: {player.get_cards_string()}"
            if retry_count < self.max_retries:
                return self._get_agent_play_with_tools(
                    agent, player, game_state, card_tracker,
                    retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                    phase=phase, tool_result=tool_result, error_msg=error_msg
                )
            return False, "Invalid series", accumulated_errors, "".join(cards)

        # Check if can beat table
        if game_state.table_series.type != CardType.INVALID:
            can_beat, reason = series.can_beat(game_state.table_series)
            if not can_beat:
                accumulated_errors += 1
                attempted = "".join(cards)
                error_msg = f"❌ 无法压过桌上: {attempted}\n原因: {reason}\n桌上有: {game_state.table_series}\n需要出更大的同类型牌或炸弹。"
                if retry_count < self.max_retries:
                    return self._get_agent_play_with_tools(
                        agent, player, game_state, card_tracker,
                        retry_count=retry_count + 1, accumulated_errors=accumulated_errors,
                        phase=phase, tool_result=tool_result, error_msg=error_msg
                    )
                attempted = "".join([str(c) for c in selected_cards])
                return False, f"Cannot beat table: {reason}", accumulated_errors, attempted

        return True, selected_cards, accumulated_errors, ""
    
    def _format_game_start(self) -> str:
        """Format game start message"""
        lines = ["游戏开始!"]
        for p in self.players:
            role = "【地主】" if p.is_landlord else "【农民】"
            lines.append(f"{p.name}{role}: {len(p.cards)}张牌")
        return "\n".join(lines)
    
    def _execute_tool_for_agent(self, tool_name: str, player: Player,
                                 game_state: GameState, card_tracker: CardTracker) -> str:
        """
        Execute a tool and return the result as a string.
        
        Args:
            tool_name: Name of the tool to execute
            player: Current player
            game_state: Current game state
            card_tracker: Card tracking info
        
        Returns:
            Tool result as a string
        """
        from tools import ToolResult
        
        # Map tool names to their execution functions
        tool_executors = {
            # CardHistoryTool methods
            "get_played_cards": lambda: CardHistoryTool.get_played_cards(
                card_tracker.played_cards if card_tracker else {},
                target_player=None
            ),
            "get_remaining_deck": lambda: CardHistoryTool.get_remaining_deck(
                card_tracker.get_remaining_deck_composition() if card_tracker else {}
            ),
            # ValidMovesTool methods
            "get_valid_moves": lambda: ValidMovesTool.get_valid_moves(
                player, game_state.table_series, game_state=game_state
            ),
            "get_direct_recommendation": lambda: ValidMovesTool.get_direct_recommendation(
                player, game_state
            ),
            # TreeSearchTool methods
            "find_best_play": lambda: TreeSearchTool.find_best_play(
                player.cards, game_state.table_series, player.is_landlord
            ),
        }
        
        if tool_name not in tool_executors:
            return f"[错误: 未知工具 '{tool_name}'。可用工具: {', '.join(tool_executors.keys())}]"
        
        try:
            result: ToolResult = tool_executors[tool_name]()
            return result.result if result else "[工具返回空结果]"
        except Exception as e:
            return f"[工具执行错误: {str(e)}]"


def run_single_game(agents: List[BaseAgent], random_landlord: bool = True,
                    verbose: bool = True) -> GameResult:
    """Convenience function to run a single game."""
    runner = GameRunner(agents, verbose=verbose)
    return runner.run_game(random_landlord=random_landlord)


def run_multiple_games(agents: List[BaseAgent], num_games: int = 10,
                       random_landlord: bool = True, verbose: bool = False,
                       enable_logging: bool = False, log_folder: str = "logs",
                       experiment_name: str = None) -> List[GameResult]:
    """
    Run multiple games and collect results.
    """
    results = []
    aggregated_tool_calls: Dict[str, int] = {}

    for i in range(num_games):
        if verbose or i % 10 == 0:
            print(f"Running game {i+1}/{num_games}...")

        # Reset agents between games
        for agent in agents:
            agent.history = []

        runner = GameRunner(
            agents, verbose=False,
            enable_logging=enable_logging,
            log_folder=log_folder,
            experiment_name=experiment_name
        )
        result = runner.run_game(random_landlord=random_landlord)
        results.append(result)

        # Aggregate tool calls
        for tool_name, count in result.tool_call_counts.items():
            aggregated_tool_calls[tool_name] = aggregated_tool_calls.get(tool_name, 0) + count

    # Print experiment-level tool call summary
    if aggregated_tool_calls:
        print("\n" + "=" * 50)
        print("实验工具调用统计")
        print("=" * 50)
        total_calls = sum(aggregated_tool_calls.values())
        print(f"总工具调用次数: {total_calls}")
        print(f"平均每局调用: {total_calls / num_games:.1f} 次")
        print("")

        # Sort by count descending
        sorted_tools = sorted(aggregated_tool_calls.items(), key=lambda x: x[1], reverse=True)
        for tool_name, count in sorted_tools:
            percentage = (count / total_calls) * 100 if total_calls > 0 else 0
            avg_per_game = count / num_games
            print(f"  {tool_name:30s}: {count:4d} 次 ({percentage:5.1f}%) - 平均每局 {avg_per_game:.1f} 次")
        print("=" * 50)

    return results
