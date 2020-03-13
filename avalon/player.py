from .enums import Position, Faction
from .constant import POSITION_NAME_LIST, POSITION_IMAGE_LIST, EMOJI, QEMOJI

class Player:

    def __init__(self, user):
        self.user = user  # discord User
        self.position = Position.LoyalServant1  # 玩家身分
        self.index = 0 # 玩家索引
        self.lake_target = None  # 使用湖中女神查驗的對象
        self.assassinate_target = None  # 剌殺的對象

    @property
    def serial_number(self):
        return self.index + 1

    @property
    def faction(self):
        if self.position == Position.Merlin or self.position == Position.Percival or self.position.value >= 7:
            return Faction.Arthur
        else:
            return Faction.Mordred

    @property
    def position_image(self):
        return POSITION_IMAGE_LIST[self.position]

    @property
    def position_name(self):
        return POSITION_NAME_LIST[self.position]
    
    @property
    def tag(self):
        return "`` {}{} ``".format(EMOJI[self.serial_number], self.user.display_name)
