# Import
import random

# Constants
suits = ['♠', '♥', '♣', '♦', '']
values = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '小王', '大王']

# Define
def validateDeal(cards)->bool:
    pass

def validateLate(cardsEarly, cardsLate)->bool:
    pass


# Class
class Card:
    # Constructor: input two integer: suit and value
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.id = 4 * value + suit 

    def __str__(self):
        return suits[self.suit] + values[self.value]    
    
class player:
    def __init__(self, name, cards):
        self.name = name
        self.landLord =  False
        self.cards = cards
        

    def __str__(self):
        landLordYesNo = "是" if(self.landLord) else "不是"
        return self.name + "， 有" + f"{len(self.cards)}" + "张手牌， " + landLordYesNo + "地主。"
        
    def becomeLandLord(self):
        self.landLord = True

    def playCard(self, early)-> bool:
        while True:
            print(self.name, "的手牌是", self.cards)
            play = input('请出牌（不要请输入pass）：')
            if play == 'pass':
                return False
            if len(early) == 0:
                if validateDeal(play) == True:
                    return True
                else:
                    continue
            else:
                if validateLate(early, play):
                    return True
                else:
                    continue
                
seriesType = ['', '单牌', '对子', '三张', '顺子', '连对', '飞机', '四带', '炸弹', '王炸']

class series:
    # constructor, create a serires object by the serires's type, value, amount of cards(连对，顺子), addons(三带，飞机，四带)
    def __init__(self, seriesCards, type = '违规', value = 0, amount = 0, addOn1 = 0, addOn2 = 0):
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
    
    def compare(self, other):
        return True


# Helper Functions
def seriesValidate(cards):
    values = [card.value for card in cards]
    values.sort()
    
    # For debugging
    print(values)
    
    length = len(cards)
    
    if length == 1:
        # 单牌
        return True, series(seriesCards = cards, type = '单牌', value = cards[0])
    
    if length == 2:
        # 对子 或 王炸
        if values[0] == values[1]:
            return True, series(seriesCards = cards, type = '对子', value = cards[0])
        if values[0] == 13 and values[1] == 14:
            return True, series(seriesCards = cards, type = '王炸')
        return False, series(seriesCards = cards)
    
    if length == 3:
        # 三
        if values[0] == values[1] and values[1] == values[2]:
            return True, series(seriesCards = cards, type = '三带', value = cards[0])
        return False, series(seriesCards = cards)
        
    if length == 4:
        # 三带一 或 炸弹
        if (values[0] == values[1] and values[1] == values[2] and values[2] != values[3]
            or values[1] == values[2] and values[2] == values[3] and values[3] != values[0]
            ):
            return True, series(seriesCards = cards, type = '三带', value = cards[0], addOn1 = 1)
        if values[0] == values[1] and values[1] == values[2] and values[2] == values[3]:
            return True, series(seriesCards = cards, type = '炸弹', value = cards[0])
        return False
    
    if length == 5:
        # 三带一对
        if cards[0].value == cards[1].value & cards[1].value == cards[2].value & cards[3].value == cards[4].value:
            return True
        if cards[2].value == cards[3].value & cards[3].value == cards[4].value & cards[0].value == cards[1].value:
            return True
        # 顺子
        straight = True
        for i in range(4):
            if cards[i].value != (cards[i+1].value - 1):
                straight = False
        if straight:
            return True
        return False
    

deck = [Card(suit, value) for suit in range(4) for value in range(13)]

deck.append(Card(4, 13))
deck.append(Card(4, 14))

random.shuffle(deck)

testSeries = [Card(0, 1), Card(1, 1), Card(2, 1), Card(3,0)]

success, testSeriesValidation = seriesValidate(testSeries)

if(success):
    print(testSeriesValidation)
    
else:
    print(testSeriesValidation)
