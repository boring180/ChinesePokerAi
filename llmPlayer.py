from transformers import AutoTokenizer, AutoModel
import landLord as ll
tokenizer = AutoTokenizer.from_pretrained("./chatglm-6b-int4", trust_remote_code=True, revision="v1.1.0")
model = AutoModel.from_pretrained("./chatglm-6b-int4", trust_remote_code=True, revision="v1.1.0").quantize(4).half().cuda()
model = model.eval()
response, history = model.chat(tokenizer, "你好！", history=[])
print(response)

players = [ll.player('玩家一'), ll.player('玩家二'), ll.player('玩家三')]
landLordNumber, gameStartMessage = ll.landlordDecide(players, ll.gameStart(players))
