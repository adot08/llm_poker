# poker_engine.py
import random
from collections import defaultdict
from itertools import combinations
from typing import List, Dict, Any

# --- 1. 定义基本元素：牌、牌组 ---
SUITS = '♠♥♦♣'
RANKS = '23456789TJQKA'
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS, 2)}

class Card:
    def __init__(self, rank, suit):
        if rank not in RANKS or suit not in SUITS: raise ValueError("无效的牌")
        self.rank, self.suit, self.value = rank, suit, RANK_VALUES[rank]
    def __str__(self): return f"{self.rank}{self.suit}"
    def __repr__(self): return self.__str__()
    def __lt__(self, other): return self.value < other.value

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for rank in RANKS for suit in SUITS]
        self.shuffle()
    def shuffle(self): random.shuffle(self.cards)
    def deal(self, n=1):
        if len(self.cards) < n: raise ValueError("牌不够了")
        return [self.cards.pop() for _ in range(n)]

# --- 2. 定义玩家 ---
class Player:
    def __init__(self, name: str, chips: int, llm_type: str):
        self.name = name
        self.initial_chips = chips
        self.llm_type = llm_type
        self.chips_at_start_of_hand = chips
        self.reset_for_new_game()

    def reset_for_new_game(self):
        self.chips = self.initial_chips
        self.hand = []
        self.reset_for_new_hand()

    def reset_for_new_hand(self):
        self.hand = []
        self.is_active = True
        self.is_all_in = False
        self.bet_in_round = 0
        self.bet_in_hand = 0
        self.chips_at_start_of_hand = self.chips

    def __str__(self): return f"{self.name} ({self.chips}筹码, {self.llm_type})"
    def __repr__(self): return self.name

# --- 3. 核心：游戏引擎 ---
class PokerGame:
    def __init__(self, players_with_llm: List[dict], starting_chips: int, small_blind: int, big_blind: int):
        self.players = [Player(p['name'], starting_chips, p['llm_type']) for p in players_with_llm]
        self.num_players = len(self.players)
        self.small_blind, self.big_blind = small_blind, big_blind
        self.deck = Deck()
        self.dealer_pos = -1
        self._reset_hand_state()

    def _reset_hand_state(self):
        self.community_cards = []
        self.pots = []
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        self.action_player_idx = -1
        self.last_raiser = None

    def start_new_hand(self):
        # 移除筹码为0的玩家
        self.players = [p for p in self.players if p.chips > 0]
        self.num_players = len(self.players)
        if self.num_players < 2: return False

        self._reset_hand_state()
        for p in self.players: p.reset_for_new_hand()

        self.deck = Deck()
        self.dealer_pos = (self.dealer_pos + 1) % self.num_players
        
        for p in self.players: p.hand = self.deck.deal(2)
        return True

    def deal_community(self, count): self.community_cards.extend(self.deck.deal(count))

    def get_player(self, index: int) -> Player: return self.players[index % self.num_players]

    def get_next_active_player_idx(self, start_idx: int) -> int:
        idx = (start_idx + 1) % self.num_players
        while True:
            player = self.get_player(idx)
            if player.is_active and not player.is_all_in: return idx
            if idx == start_idx: return -1
            idx = (idx + 1) % self.num_players

    def start_betting_round(self, round_name: str):
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        self.last_raiser = None
        for p in self.players: p.bet_in_round = 0

        if round_name == "preflop":
            sb_pos = self.get_next_active_player_idx(self.dealer_pos)
            self.small_blind_pos = sb_pos
            self._execute_bet(self.get_player(sb_pos), self.small_blind)

            bb_pos = self.get_next_active_player_idx(sb_pos)
            self.big_blind_pos = bb_pos
            self._execute_bet(self.get_player(bb_pos), self.big_blind)
            
            # Preflop中，大盲的强制下注不应被视为“最后的加注者”
            # 只有当有玩家真正raise后，才设置last_raiser
            self.action_player_idx = self.get_next_active_player_idx(bb_pos)
        else:
            self.action_player_idx = self.get_next_active_player_idx(self.dealer_pos)

    def handle_action(self, player: Player, action: str, amount: int = 0):
        if action == "fold":
            player.is_active = False
            return f"{player.name} 弃牌"
        if action == "check": return f"{player.name} 过牌"
        if action == "call":
            to_call = self.current_bet - player.bet_in_round
            bet_amount = min(to_call, player.chips)
            self._execute_bet(player, bet_amount)
            return f"{player.name} 跟注 {bet_amount}"
        if action == "raise":
            bet_amount = amount - player.bet_in_round
            self._execute_bet(player, bet_amount)
            self.min_raise_amount = amount - self.current_bet
            self.last_raiser = player
            return f"{player.name} 加注到 {amount}"
        if action == "all-in":
            bet_amount = player.chips
            # 如果是跟注all-in
            if bet_amount <= self.current_bet - player.bet_in_round:
                 self._execute_bet(player, bet_amount)
                 return f"{player.name} 跟注并All-in {bet_amount}"
            # 如果是加注all-in
            else:
                total_bet = bet_amount + player.bet_in_round
                self.min_raise_amount = max(self.min_raise_amount, total_bet - self.current_bet)
                self.last_raiser = player
                self._execute_bet(player, bet_amount)
                return f"{player.name} All-in {bet_amount}"

    def _execute_bet(self, player: Player, amount: int):
        final_amount = min(amount, player.chips)
        player.chips -= final_amount
        player.bet_in_round += final_amount
        player.bet_in_hand += final_amount
        self.current_bet = max(self.current_bet, player.bet_in_round)
        if player.chips == 0: player.is_all_in = True

    def collect_bets_and_manage_pots(self):
        all_bets = sorted([(p, p.bet_in_hand) for p in self.players if p.bet_in_hand > 0], key=lambda x: x[1])
        
        pots = []
        last_bet_level = 0
        
        for player, total_bet in all_bets:
            if total_bet > last_bet_level:
                pot_level = total_bet - last_bet_level
                pot_players = {p for p, bet in all_bets if bet >= total_bet}
                pots.append({'amount': pot_level * len(pot_players), 'eligible_players': pot_players})
                last_bet_level = total_bet

        # Merge new contributions into existing pots
        if not self.pots:
            self.pots = pots
        else:
            # This logic is complex. For now, a simpler full recalculation at the end is safer
            pass

        # Full recalculation approach (safer)
        self.pots = []
        players_in_hand = [p for p in self.players if p.bet_in_hand > 0]
        if not players_in_hand: return
        
        bet_levels = sorted(list(set(p.bet_in_hand for p in players_in_hand if p.is_all_in)))

        last_level = 0
        for level in bet_levels:
            pot_amount = 0
            eligible_players = set()
            for p in players_in_hand:
                contribution = min(max(0, p.bet_in_hand - last_level), level - last_level)
                if contribution > 0:
                    pot_amount += contribution
                    eligible_players.add(p)
            if pot_amount > 0:
                self.pots.append({'amount': pot_amount, 'eligible_players': eligible_players})
            last_level = level

        # Main pot for remaining bets
        main_pot_amount = 0
        main_pot_players = set()
        for p in players_in_hand:
            contribution = max(0, p.bet_in_hand - last_level)
            if contribution > 0:
                main_pot_amount += contribution
                main_pot_players.add(p)
        if main_pot_amount > 0:
            self.pots.append({'amount': main_pot_amount, 'eligible_players': main_pot_players})

    def determine_winners(self):
        results = []
        for pot in self.pots:
            eligible = [p for p in pot['eligible_players'] if p.is_active]
            if not eligible: continue
            if len(eligible) == 1:
                winners, best_hand_details = eligible, ("未摊牌", "")
            else:
                best_rank, winners, best_hand_details = (-1,), [], None
                for player in eligible:
                    rank, details = self._get_best_hand(player)
                    if rank > best_rank:
                        best_rank, winners, best_hand_details = rank, [player], details
                    elif rank == best_rank:
                        winners.append(player)
            results.append({'pot': pot, 'winners': winners, 'hand_details': best_hand_details})
        return results

    def _get_best_hand(self, player):
        all_seven = self.community_cards + player.hand
        best_rank, best_details = (-1,), None
        for combo in combinations(all_seven, 5):
            rank, details = self._evaluate_hand(list(combo))
            if rank > best_rank:
                best_rank, best_details = rank, details
        return best_rank, best_details

    def distribute_winnings(self, winner_results):
        for res in winner_results:
            pot_amt, winners = res['pot']['amount'], res['winners']
            share, rem = pot_amt // len(winners), pot_amt % len(winners)
            for w in winners: w.chips += share
            if rem > 0:
                sorted_winners = sorted(winners, key=lambda p: (self.players.index(p) - self.dealer_pos -1 + self.num_players) % self.num_players)
                for i in range(rem): sorted_winners[i].chips += 1

    def _evaluate_hand(self, hand):
        values = sorted([c.value for c in hand], reverse=True)
        suits = [c.suit for c in hand]
        is_straight = len(set(values)) == 5 and (max(values) - min(values) == 4)
        if values == [14, 5, 4, 3, 2]: is_straight, values = True, [5, 4, 3, 2, 1]
        is_flush = len(set(suits)) == 1
        counts = sorted([(v, values.count(v)) for v in set(values)], key=lambda x: (x[1], x[0]), reverse=True)
        vals_by_count = [v[0] for v in counts]
        counts_dict = dict(counts)

        if is_straight and is_flush: return (9, values[0]), ("皇家同花顺" if values[0]==14 else "同花顺", sorted(hand, reverse=True))
        if counts[0][1] == 4: return (8, vals_by_count), ("四条", sorted(hand, key=lambda c: (counts_dict.get(c.value, 0), c.value), reverse=True))
        if counts[0][1] == 3 and counts[1][1] == 2: return (7, vals_by_count), ("葫芦", sorted(hand, key=lambda c: (counts_dict.get(c.value, 0), c.value), reverse=True))
        if is_flush: return (6, values), ("同花", sorted(hand, reverse=True))
        if is_straight: return (5, values[0]), ("顺子", sorted(hand, reverse=True))
        if counts[0][1] == 3: return (4, vals_by_count), ("三条", sorted(hand, key=lambda c: (counts_dict.get(c.value, 0), c.value), reverse=True))
        if counts[0][1] == 2 and counts[1][1] == 2: return (3, vals_by_count), ("两对", sorted(hand, key=lambda c: (counts_dict.get(c.value, 0), c.value), reverse=True))
        if counts[0][1] == 2: return (2, vals_by_count), ("一对", sorted(hand, key=lambda c: (counts_dict.get(c.value, 0), c.value), reverse=True))
        return (1, values), ("高牌", sorted(hand, reverse=True))