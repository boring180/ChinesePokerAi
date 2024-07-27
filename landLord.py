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
    
    def compare(self, lower):
        if lower.type == '违规' or self.type == '违规':
            return False
        print("HW")
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
    print(values)
    
    length = len(cards)
    
    match length:
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
                return series(seriesCards = cards, type = '三带', value = values[0], addOn1 = 1)
            if values[0] == values[1] and values[1] == values[2] and values[2] == values[3]:
                return series(seriesCards = cards, type = '炸弹', value = values[0])
    
        case 5:
            # 三带一对
            if (values[0] == values[1] and values[1] == values[2] and values[2] != values[3] and values[3] == values[4]
                or values[2] == values[3] and values[3] == values[4] and values[4] != values[0] and values[0] == values[1]
                ):
                return series(seriesCards = cards, type = '三带', value = values[0], amount = length)
            
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
    

deck = [Card(suit, value) for suit in range(4) for value in range(13)]

deck.append(Card(4, 13))
deck.append(Card(4, 14))

random.shuffle(deck)

testSeries1 = series([Card(0, 1)])
print(testSeries1)
testSeries2 = series([Card(0, 2)])
print(testSeries2)

print(testSeries1.compare(testSeries2))