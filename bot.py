
import discord
import asyncio
import sqlite3
import string
import random
import traceback

from character import Character
from exceptions import FeedbackError


class Bot():
	def __init__(self, debug=True):
		self.debug = debug
		self.confirming = None

		self.commands = [
			("roll",self.roll),
			("add char",self.add_char),
			("view",self.view)
		]

		self.view_commands = [
			("characters",self.view_characters),
			("chars",self.view_characters)
		]
		
		if not debug:
			self.setup_db()
			self.setup_discord()

	# PROPERTIES

	@property
	def characters(self):
		cur = self.db.execute("SELECT rowid,name,char_id FROM characters WHERE active = 1 ORDER BY char_id")
		chars = cur.fetchall()
		cur.close()
		return [Character(self,c[1],c[0]) for c in chars]

	# SETUP

	def setup_db(self):
		con = self.db = sqlite3.connect("db.db")
		schema = {
			"characters (name text, active int, char_id text, player_id text, dice_pool text)",
			"moves (char_id text, dice text, name text)",
			"consequences (char_id text, dice text, name text)"
		}

		for t in schema:
			try:
				con.execute("CREATE TABLE IF NOT EXISTS "+t)
			except Exception as e:
				self.log("Error with SQL:\n"+t+"\n"+str(e))
				break

		con.commit()

	def setup_discord(self):
		intents = discord.Intents.default()
		intents.members = True
		self.client = discord.Client(intents=intents)

	def start_bot(self,token):
		self.client.run(token)

	# UTIL

	def log(self, m):
		print(m)

	def debug_log(self, m):
		if self.debug:
			self.log(m)

	def get_next_char_id(self):
		chars = string.ascii_uppercase+string.ascii_lowercase
		
		cur = self.db.execute("SELECT char_id FROM characters WHERE active = 1 ORDER BY char_id")
		char_ids = [c[0] for c in cur.fetchall()]
		cur.close()
		
		for char in chars:
			if char not in char_ids:
				return char
		
		raise FeedbackError("Too many active characters!")

	# EVENTS

	async def on_ready(self):
		self.log('DOGSbot ready')

	async def on_message(self,m):
		if m.author.bot:
			return

		self.log('got a message: '+m.content)

		try:
			if m.content.startswith('dq '):
				await self.parse_command(m)
			elif m.content.startswith('Y') and self.confirming:
				await self.confirm(m)
			elif m.content.startswith('n') and self.confirming:
				await self.deny(m)

		except FeedbackError as e:
			await m.reply(f"ERROR: {e}")

		except Exception as e:
			self.log(traceback.format_exc())
			await m.reply(f"UNCAUGHT ERROR: {e}")


	# COMMAND PARSING

	async def parse_command(self,m):
		for command,method in self.commands:
			if m.content[3:].startswith(command):
				await method(m)
				return

	async def view(self,m):
		for command,method in self.view_commands:
			if m.content[8:].startswith(command):
				await method(m)
				return

	async def confirm(self,m):
		pass

	async def deny(self,m):
		pass


	# RESPONSE FORMATTING
	
	# select active chars + print them in order of char_id
	@property
	def char_list(self):
		return "\n".join([f"{c.char_id} - {c.name}" for c in self.characters])

	# COMMANDS

	async def roll(self,m):
		amt, die = m.content[8:].split('d')
		
		try:
			amt = int(amt)
			die = int(die)
			if amt < 1 or die < 1:
				raise
		except Exception as e:
			raise FeedbackError("Invalid roll!")

		rolls = [random.randint(1,die) for i in range(amt)]
		rolls = sorted(rolls, key=lambda x: 0-x)
		total = sum(rolls)
		rlist = ' + '.join([str(r) for r in rolls])

		reply = f"{total} = {rlist}" if len(rolls) > 1 else total
		reply = f"Rolled {amt}d{die}: {reply}"

		await m.reply(reply)

	async def add_char(self,m):
		name = m.content[12:]
		char = Character(self, name)
		await m.reply(f"Added {name} ({char.char_id}) to the game!\n\n{self.char_list}")

	async def view_characters(self,m):
		await m.reply(self.char_list)


