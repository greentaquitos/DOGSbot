
import discord
import asyncio


class Bot():
	def __init__(self, debug=True):
		self.debug = debug
		
		if not debug:
			self.setup_bot()

	def setup_bot(self):
		intents = discord.Intents.default()
		intents.members = True
		self.client = discord.Client(intents=intents)

	def start_bot(self,token):
		self.client.run(token)

	def log(self, m):
		print(m)

	def debug_log(self, m):
		if self.debug:
			self.log(m)

	async def on_ready(self):
		self.log('ready')

	async def on_message(self,m):
		self.log('got a message: '+m.content)
		if m.content.startswith('dq'):
			m.reply("Hi there!")
