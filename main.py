
from config import TOKEN
from bot import Bot

global b


if __name__ == "__main__":
    b = Bot(False)
else:
	exit()

@b.client.event
async def on_ready():
	await b.on_ready()

@b.client.event
async def on_message(message):
	await b.on_message(message)

b.start_bot(TOKEN)
