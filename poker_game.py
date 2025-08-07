"""
德州扑克游戏引擎 - 使用poker库处理游戏逻辑
"""

from poker import Card, Hand, Range
from typing import List, Dict, Optional, Tuple
import random
from enum import Enum


class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all-in"


class Player:
    def __init__(self, name: str, chips: int, llm_type: str = "qwen3"):
        self.name = name
        self.chips = chips
        self.hand = []
        self.is_active = True
        self.is_all_in = False
        self.current_bet = 0
        self.llm_type = llm_type
        
    def reset_hand(self):
        """重置玩家手牌"""
        self.hand = []
        self.is_active = True
        self.is_all_in = False
        self.current_bet = 0


class PokerGame:
    def __init__(self, num_players: int = 4, starting_chips: int = 1000):
        self.num_players = num_players
        self.starting_chips = starting_chips
        self.players = []
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.small_blind = 10
        self.big_blind = 20
        self.dealer_pos = 0
        self.current_player = 0
        self.round_name = "preflop"
        self.deck = []
        
        self._initialize_players()
        self._initialize_deck()
    
    def _initialize_players(self):
        """初始化玩家"""
        llm_types = ["qwen3", "qwen2.5"]
        for i in range(self.num_players):
            llm_type = llm_types[i % len(llm_types)]
            player = Player(f"Player_{i+1}", self.starting_chips, llm_type)
            self.players.append(player)
    
    def _initialize_deck(self):
        """初始化牌组"""
        self.deck = []
        suits = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        
        for suit in suits:
            for rank in ranks:
                self.deck.append(Card(f"{rank}{suit}"))
        
        random.shuffle(self.deck)
    
    def deal_cards(self):
        """发手牌"""
        for player in self.players:
            if player.is_active:
                player.hand = [self.deck.pop(), self.deck.pop()]
    
    def deal_community_cards(self, count: int):
        """发公共牌"""
        for _ in range(count):
            self.community_cards.append(self.deck.pop())
    
    def get_game_state_text(self) -> str:
        """获取纯文本游戏状态"""
        state = f"""
=== 德州扑克游戏状态 ===
轮次: {self.round_name}
底池: {self.pot} 筹码
当前下注: {self.current_bet} 筹码
公共牌: {self._cards_to_text(self.community_cards)}

位置信息:
  庄家: {self.players[self.dealer_pos].name}
  小盲: {self.players[self.small_blind_pos].name}
  大盲: {self.players[self.big_blind_pos].name}

玩家状态:
"""
        
        for i, player in enumerate(self.players):
            if player.is_active:
                # 添加位置标识
                position = ""
                if i == self.dealer_pos:
                    position = "(庄家)"
                elif i == self.small_blind_pos:
                    position = "(小盲)"
                elif i == self.big_blind_pos:
                    position = "(大盲)"
                
                status = "全下" if player.is_all_in else f"下注: {player.current_bet}"
                state += f"  {player.name}{position}: {player.chips} 筹码, {status}\n"
        
        return state
    
    def _cards_to_text(self, cards: List[Card]) -> str:
        """将牌转换为文本表示"""
        if not cards:
            return "无"
        return " ".join([str(card) for card in cards])
    
    def get_player_hand_text(self, player: Player) -> str:
        """获取玩家手牌文本"""
        return self._cards_to_text(player.hand)
    
    def get_winner(self) -> List[Player]:
        """确定获胜者"""
        active_players = [p for p in self.players if p.is_active]
        
        if len(active_players) == 1:
            return active_players
        
        # 计算每个玩家的牌力
        player_scores = []
        for player in active_players:
            try:
                # 使用简单的牌力计算方法
                score = self._calculate_hand_strength(player.hand, self.community_cards)
                player_scores.append((player, score))
                print(f"{player.name} 牌力分数: {score}")
            except Exception as e:
                print(f"计算 {player.name} 牌力时出错: {e}")
                # 使用默认分数
                player_scores.append((player, 0))
        
        # 按分数排序
        player_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回获胜者（可能有多个平局）
        winners = [player_scores[0][0]]
        best_score = player_scores[0][1]
        
        for player, score in player_scores[1:]:
            if score == best_score:
                winners.append(player)
            else:
                break
        
        return winners
    
    def _calculate_hand_strength(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """计算手牌强度"""
        all_cards = hole_cards + community_cards
        
        # 提取牌面值和花色
        ranks = [str(card.rank) for card in all_cards]
        suits = [card.suit for card in all_cards]
        
        # 计算各种牌型
        score = 0
        
        # 1. 同花顺 (8000-9000)
        if len(community_cards) >= 3:
            flush_straight = self._check_flush_straight(all_cards)
            if flush_straight:
                score = 8000 + flush_straight
        
        # 2. 四条 (7000-7999)
        four_of_kind = self._check_four_of_kind(ranks)
        if four_of_kind:
            score = 7000 + four_of_kind
        
        # 3. 葫芦 (6000-6999)
        full_house = self._check_full_house(ranks)
        if full_house:
            score = 6000 + full_house
        
        # 4. 同花 (5000-5999)
        flush = self._check_flush(all_cards)
        if flush:
            score = 5000 + flush
        
        # 5. 顺子 (4000-4999)
        straight = self._check_straight(ranks)
        if straight:
            score = 4000 + straight
        
        # 6. 三条 (3000-3999)
        three_of_kind = self._check_three_of_kind(ranks)
        if three_of_kind:
            score = 3000 + three_of_kind
        
        # 7. 两对 (2000-2999)
        two_pair = self._check_two_pair(ranks)
        if two_pair:
            score = 2000 + two_pair
        
        # 8. 一对 (1000-1999)
        one_pair = self._check_one_pair(ranks)
        if one_pair:
            score = 1000 + one_pair
        
        # 9. 高牌 (0-999)
        high_card = self._get_high_card(ranks)
        score = max(score, high_card)
        
        return score
    
    def _rank_to_value(self, rank: str) -> int:
        """将牌面转换为数值"""
        if rank == 'A':
            return 14
        elif rank == 'K':
            return 13
        elif rank == 'Q':
            return 12
        elif rank == 'J':
            return 11
        elif rank == 'T':
            return 10
        else:
            return int(rank)
    
    def _check_flush_straight(self, cards: List[Card]) -> int:
        """检查同花顺"""
        # 简化实现，只检查同花
        return self._check_flush(cards)
    
    def _check_four_of_kind(self, ranks: List[str]) -> int:
        """检查四条"""
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        for rank, count in rank_counts.items():
            if count == 4:
                return self._rank_to_value(rank)
        return 0
    
    def _check_full_house(self, ranks: List[str]) -> int:
        """检查葫芦"""
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        three_rank = None
        two_rank = None
        
        for rank, count in rank_counts.items():
            if count == 3:
                three_rank = rank
            elif count == 2:
                two_rank = rank
        
        if three_rank and two_rank:
            return self._rank_to_value(three_rank) * 100 + self._rank_to_value(two_rank)
        return 0
    
    def _check_flush(self, cards: List[Card]) -> int:
        """检查同花"""
        suit_counts = {}
        for card in cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        
        for suit, count in suit_counts.items():
            if count >= 5:
                # 返回同花中最大的牌
                flush_cards = [card for card in cards if card.suit == suit]
                flush_cards.sort(key=lambda c: self._rank_to_value(str(c.rank)), reverse=True)
                return self._rank_to_value(str(flush_cards[0].rank))
        return 0
    
    def _check_straight(self, ranks: List[str]) -> int:
        """检查顺子"""
        values = [self._rank_to_value(rank) for rank in ranks]
        values = list(set(values))  # 去重
        values.sort()
        
        # 检查A2345顺子
        if 14 in values and 2 in values and 3 in values and 4 in values and 5 in values:
            return 5
        
        # 检查普通顺子
        for i in range(len(values) - 4):
            if values[i+4] - values[i] == 4:
                return values[i+4]
        return 0
    
    def _check_three_of_kind(self, ranks: List[str]) -> int:
        """检查三条"""
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        for rank, count in rank_counts.items():
            if count == 3:
                return self._rank_to_value(rank)
        return 0
    
    def _check_two_pair(self, ranks: List[str]) -> int:
        """检查两对"""
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        pairs = []
        for rank, count in rank_counts.items():
            if count == 2:
                pairs.append(rank)
        
        if len(pairs) >= 2:
            pairs.sort(key=lambda r: self._rank_to_value(r), reverse=True)
            return self._rank_to_value(pairs[0]) * 100 + self._rank_to_value(pairs[1])
        return 0
    
    def _check_one_pair(self, ranks: List[str]) -> int:
        """检查一对"""
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        for rank, count in rank_counts.items():
            if count == 2:
                return self._rank_to_value(rank)
        return 0
    
    def _get_high_card(self, ranks: List[str]) -> int:
        """获取高牌"""
        values = [self._rank_to_value(rank) for rank in ranks]
        return max(values) if values else 0
    
    def distribute_pot(self, winners: List[Player]):
        """分配底池"""
        if not winners:
            return
        
        amount_per_winner = self.pot // len(winners)
        for winner in winners:
            winner.chips += amount_per_winner
        
        # 处理余数
        remainder = self.pot % len(winners)
        if remainder > 0:
            winners[0].chips += remainder
        
        self.pot = 0
    
    def reset_round(self):
        """重置一轮"""
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.round_name = "preflop"
        
        for player in self.players:
            player.reset_hand()
        
        self._initialize_deck()
        
        # 移动庄家位置
        self.dealer_pos = (self.dealer_pos + 1) % self.num_players
        
        # 计算位置
        self.small_blind_pos = (self.dealer_pos + 1) % self.num_players
        self.big_blind_pos = (self.dealer_pos + 2) % self.num_players
        
        # preflop轮从大盲位置的下一个玩家开始（UTG位置）
        self.current_player = (self.big_blind_pos + 1) % self.num_players
    
    def is_round_complete(self) -> bool:
        """检查当前轮次是否完成"""
        active_players = [p for p in self.players if p.is_active and not p.is_all_in]
        
        if len(active_players) <= 1:
            return True
        
        # 检查所有活跃玩家的下注是否相等
        bet_amounts = [p.current_bet for p in active_players]
        all_equal = len(set(bet_amounts)) == 1
        
        # 调试信息
        if not all_equal:
            print(f"下注不均衡: {[(p.name, p.current_bet) for p in active_players]}")
        
        return all_equal
    
    def next_round(self):
        """进入下一轮"""
        if self.round_name == "preflop":
            self.round_name = "flop"
            self.deal_community_cards(3)
        elif self.round_name == "flop":
            self.round_name = "turn"
            self.deal_community_cards(1)
        elif self.round_name == "turn":
            self.round_name = "river"
            self.deal_community_cards(1)
        else:
            # 游戏结束
            return False
        
        # 重置下注
        self.current_bet = 0
        for player in self.players:
            player.current_bet = 0
        
        # 从庄家位置的下一个活跃玩家开始（小盲位置）
        self.current_player = self.small_blind_pos
        # 找到第一个活跃玩家
        while not self.players[self.current_player].is_active:
            self.current_player = (self.current_player + 1) % self.num_players
        
        return True 