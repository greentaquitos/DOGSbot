
from config import TOKEN
import bot

global b


if __name__ == "__main__":
    b = bot.Bot(False)
else:
	exit()

@b.client.event
async def on_ready():
	b.on_ready()
	pass

@b.client.event
async def on_message(message):
	b.on_message(message)
	pass

b.start_bot(TOKEN)
