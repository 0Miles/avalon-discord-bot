from random import shuffle, randint

from .enums import Position, Faction
from .player import Player

from .constant import POSITION_NAME_LIST, POSITION_IMAGE_LIST, EMOJI, QEMOJI

class Game:

    def __init__(self, ctx, user_dict, lady_of_the_lake_enabled=False):
        self.ctx = ctx
        self.user_dict = user_dict # discord user
        self.player_list = [Player(user_dict[key]) for key in user_dict]  # 玩家
        self.vote_count = 0  # 投票次數
        self.round = 1  # 目前遊戲進度
        self.stage = 0  # 目前遊戲階段，0普通，1刺殺，2結束
        self.leader = None  # 此round負責派任務的玩家
        self.assassin = None # 身分為刺客的玩家
        self.lady_of_the_lake_enabled = lady_of_the_lake_enabled  # 是否啟用湖中女神
        self.holding_lady = None # 持有湖中女神的玩家
        self.lake_count = 0  # 湖中女神次數

        if len(self.player_list) > 7:
            self.round_status = [3, 4, 4, 5, 5]
        elif len(self.player_list) > 6:
            self.round_status = [2, 3, 3, 4, 4]
        elif len(self.player_list) > 5:
            self.round_status = [2, 3, 4, 3, 4]
        else:
            self.round_status = [2, 3, 2, 3, 3]

    @property
    def vote_status(self):
        return str.join(" ", [EMOJI["full"]] * self.vote_count + [EMOJI["space"]] * (5 - self.vote_count))

    @property
    def status(self):
        return str.join(" ", [EMOJI[status] for status in self.round_status])

    @property
    def number_of_people(self):
        return self.round_status[self.round - 1]

    @property
    def total_player_count(self):
        return len(self.player_list)

    @property
    def round4need2fail(self):
        if len(self.player_list) > 6:
            return True
        else:
            return False
    
    @property
    def result(self):
        if self.vote_count < 5 and self.round_status.count("fail") < 3 and self.round_status.count("success") < 3:
            return "ongoing"
        elif self.vote_count > 4 or self.round_status.count("fail") > 2 or self.assassin.assassinate_target is not None and self.assassin.assassinate_target.position == Position.Merlin:
            return Faction.Mordred
        else:
            return Faction.Arthur

    def deal(self):
        if self.total_player_count > 9:
            position_list = [3, 4, 5, 6, 1, 2]
        elif self.total_player_count > 6:
            position_list = [3, 4, 5, 1, 2]
        elif self.total_player_count > 4:
            position_list = [3, 4, 1, 2]
        else:
            position_list = [4]

        position_list += [i for i in range(7, 7 + self.total_player_count - len(position_list))]
        shuffle(self.player_list)
        shuffle(position_list)

        temp_index = 0
        for player in self.player_list:
            player.index = temp_index
            temp_index += 1

            player.position = Position(position_list.pop())
            if player.position == Position.Assassin:
                self.assassin = player
        
        if self.lady_of_the_lake_enabled:
            self.holding_lady = self.player_list[self.total_player_count - 1]
        
        self.leader = self.player_list[0]

    def next_leader(self):
        leader_index = self.leader.index + 1
        if leader_index > self.total_player_count - 1:
            leader_index = 0
        self.leader = self.player_list[leader_index]
    
    def next_round(self):
        self.round += 1
