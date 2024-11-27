# For llamaPlayer
# from transformers import AutoTokenizer, AutoModel 

import landLord as ll


# tokenizer = AutoTokenizer.from_pretrained("./chatglm-6b-int4", trust_remote_code=True, revision="v1.1.0")
# model = AutoModel.from_pretrained("./chatglm-6b-int4", trust_remote_code=True, revision="v1.1.0").quantize(4).half().cuda()
# model = model.eval()
# response, history = model.chat(tokenizer, "你好！", history=[])
# print(response)

introductionMessage = "你是一个打斗地主的人工智能，这个游戏版本没有飞机和四带，其他和斗地主的经典玩法相同。"

players = [ll.player('玩家一'), ll.player('玩家二'), ll.player('玩家三')]
landLordNumber, gameStartMessage = ll.landlordDecide(players, ll.gameStart(players))
print(gameStartMessage)

playing = landLordNumber
table = ll.series()
gameHistory = gameStartMessage
passCount = 0

while(True):
    if passCount == 1:
        table = ll.series()
    playerOutput = '玩家' + ll.chineseNumber[playing]
    while True:
        playerMessage = players[playing].playerTurn(table)
        playerResponse, history = model.chat(tokenizer, introductionMessage + playerMessage, history=[])
        print(playerResponse)
        if 'PASS' in playerResponse and table.type != '违规':
            passCount += 1
            playerOutput += ' 跳过'
            break
        playerResponseSeries, playerResponseCards = players[playing].cardsValid(playerResponse,table)
        if table.compare(playerResponseSeries):
            table = playerResponseSeries
            playerOutput = playerResponseSeries
            players[playing].castCards(playerResponseCards)
            break

    print(playerOutput)

    gameEnd, winner = ll.gameEnd(players)

    if gameEnd:
        print("玩家" + ll.chineseNumber[winner] + " 获胜！")
        break
