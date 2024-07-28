# Import
import random
import os

# Constants
suits = ['♠', '♥', '♣', '♦', '']
values = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '小王', '大王']

# Define
def validateDeal(cards)->bool:
    pass

def validateLate(cardsEarly, cardsLate)->bool:
    pass

# Ramdom seed

# Class
class Card:
    # Constructor: input two integer: suit and value
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.id = 4 * value + suit 

    def __str__(self):
        return suits[self.suit] + values[self.value]
    
    def getID(self):
        return self.id
    
def readCardId(card):
    return card.getID()
    
class player:
    def __init__(self, name):
        self.name = name
        self.landLord =  False
    
    def cardsAssign(self, cards):
        cards.sort(key = readCardId)
        self.cards = cards

    def __str__(self):
        landLordYesNo = "是" if(self.landLord) else "不是"
        return self.name + "， 有" + f"{len(self.cards)}" + "张手牌， " + landLordYesNo + "地主。"
        
    def becomeLandLord(self,deckAppend):
        self.landLord = True
        self.cards.extend(deckAppend)
        self.cards.sort(key = readCardId)
        
    def isLandLord(self):
        return self.landLord
    
    def gameStartMessage(self):
        return '你是:' + self.name + ' 你的手牌是:' +  self.getCardsString() 
        
    def isWin(self):
        return len(self.cards) == 0
    
    def cardsValid(self, cast, early):
        cards = []
        for i in range (len(self.cards)):
            if (f"{self.cards[i]}" in cast):
                cards.append[self.cards[i]]
        return early.compare(seriesValidate(cards))
    
    def castCards(self, cast):
        for i in range (len(cast)):
            self.cards.remove(cast[i])

    
    def getCardsString(self):
        seriesString = ''
        for  i in range(len(self.cards)):
            seriesString += str(self.cards[i])
        return seriesString

                
seriesType = ['', '单牌', '对子', '三张', '顺子', '连对', '飞机', '四带', '炸弹', '王炸']

class series:
    # constructor, create a serires object by the serires's type, value, amount of cards(连对，顺子), addons(三带，飞机，四带)
    def __init__(self, seriesCards = [], type = '违规', value = 0, amount = 0, addOn1 = 0, addOn2 = 0):
        self.seriesCards = seriesCards
        self.type = type
        self.value = value
        self.amount = amount
        self.addOn1 = addOn1
        self.addOn2 = addOn2
    
    def __str__(self):
        seriesString = ''
        for  i in range(len(self.seriesCards)):
            seriesString += str(self.seriesCards[i])
        return '牌型：' + self.type + ' ' + seriesString
    
    def compare(self, lower):
        if lower.type == '违规' or self.type == '违规':
            return False
        if lower.type == '王炸':
            return True
        if self.type == '王炸':
            return False
        if lower.type == '炸弹' and self.type != '炸弹':
            return True
        if lower.type != '炸弹' and self.type == '炸弹':
            return False
        if lower.type != self.type or lower.amount != self.amount or lower.addOn1 != self.addOn1 or lower.addOn2 != self.addOn2:
            return False
        return lower.value > self.value


# Helper Functions
def seriesValidate(cards):
    values = [card.value for card in cards]
    values.sort()
    
    # For debugging
    # print(values)
    
    length = len(cards)
    
    match length:
        case 0:
            # 空
            return series(seriesCards = cards)
        
        case 1:
            # 单牌
            return series(seriesCards = cards, type = '单牌', value = values[0])
    
        case 2:
            # 对子 或 王炸
            if values[0] == values[1]:
                return series(seriesCards = cards, type = '对子', value = values[0])
            if values[0] == 13 and values[1] == 14:
                return series(seriesCards = cards, type = '王炸')
    
        case 3:
            # 三
            if values[0] == values[1] and values[1] == values[2]:
                return series(seriesCards = cards, type = '三带', value = values[0])
        
        case 4:
            # 三带一 或 炸弹
            if (values[0] == values[1] and values[1] == values[2] and values[2] != values[3]
                or values[1] == values[2] and values[2] == values[3] and values[3] != values[0]
                ):
                return series(seriesCards = cards, type = '三带', value = values[1], addOn1 = 1)
            if values[0] == values[1] and values[1] == values[2] and values[2] == values[3]:
                return series(seriesCards = cards, type = '炸弹', value = values[0])
    
        case 5:
            # 三带一对
            if (values[0] == values[1] and values[1] == values[2] and values[2] != values[3] and values[3] == values[4]
                or values[2] == values[3] and values[3] == values[4] and values[4] != values[0] and values[0] == values[1]
                ):
                return series(seriesCards = cards, type = '三带', value = values[2], amount = length)
            
        #case 6:
            # 四带二
            # 飞机不带
        #    pass
        
        #case 8:
            # 四带两对
            # 飞机带单牌
        #    pass
        
        #case 9:
            # 三个翅膀的飞机
        #    pass
        
        #case 10:
            # 飞机带两对
        #    pass
            
        #case 12:
            # 三个翅膀的飞机带单牌
            # 四个翅膀的飞机
        #    pass
            
        #case 15:
            # 三个翅膀的飞机带对牌
            # 五个翅膀的飞机
        #    pass
        
        #case 16:
            # 四个翅膀的飞机带单牌
        #    pass
            
        #case 18:
            # 六个翅膀的飞机
        #    pass
        
        #case 20:
            # 四个翅膀的飞机带对牌
        #    pass
        
    # 顺子，连对 不能以2结尾
    if values[length-1] == 12:
        return series(seriesCards = cards)
    
    # 顺子
    if length > 4:
        straight = True
    else:
        straight = False
        
    for i in range(length):
        if i > 0 and values[i] != values[i-1] + 1:
            straight = False
    if straight:
            return series(seriesCards = cards, type = '顺子', value = values[length-1], amount = length)
        
    # 连对
    if length > 5 and length % 2 == 0:
        straightPairs = True
    else:
        straightPairs = False
    for i in range(length):
        if i  == 0:
            continue
        if i % 2 == 1 and values[i] != values[i - 1]:
            straightPairs = False
        if i % 2 == 0 and values[i] != values[i - 2] + 1:
            straightPairs = False

    if straightPairs:
            return series(seriesCards = cards, type = '连对', value = values[length-1], amount = length)
        
    # 错误牌型
    return series(seriesCards = cards)
    
players = [player('玩家一'), player('玩家二'), player('玩家三')]

# Game start
# Parameters:
#   Players: list of the players of the game
# Return:
#   The landlord cards of the game
def gameStart(players):
    deck = [Card(suit, value) for suit in range(4) for value in range(13)]
    deck.append(Card(4, 13))
    deck.append(Card(4, 14))

    random.shuffle(deck)

    players[0].cardsAssign(deck[0:17])
    players[1].cardsAssign(deck[17:34])
    players[2].cardsAssign(deck[34:51])

    return deck[51:54]

# landlordDecide
# Parameters:
#   players: list of the players of the game
#   landLordCards: The extrea three cards of the landlord
#   landLordNumer: Which player will be the landlord
#   rand: Whether to use random decision on landlord assign
# Return:
#   The message output after the landlord is decided
#   The landLordNumer
def landlordDecide(players, landLordCards, landLordNumber = 0, rand = True):
    if rand:
        landLordNumber = random.randrange(3)
    
    players[landLordNumber].becomeLandLord(landLordCards)

    return landLordNumber, f"{players[0]}" + f"{players[1]}" + f"{players[2]}" + "地主牌：" + f"{landLordCards[0]}" + f"{landLordCards[1]}" + f"{landLordCards[2]}"

# cardDisplay
# Parameters:
#   Cards: The cards to display
# Return:
#   The string repsentation of the cards
def cardsDisplay(cards):
    seriesString = ''
    for  i in range(len(cards)):
        seriesString += str(cards[i])
        return seriesString

# gameEnd
# Parameters:
#   players: list of the players of the game
# Return:
#   game end or not
#   the index of the winner
def gameEnd(players):
    if players[0].isWin():
        return True, 0
    if players[1].isWin():
        return True, 1
    if players[2].isWin():
        return True, 2
    return False, 0
    
landLordNumber, gameStartMessage = landlordDecide(players, gameStart(players))

print(gameStartMessage)

print(players[0].getCardsString())

