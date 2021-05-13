
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
			("+c",self.add_consequence),
			("+m",self.add_move),
			("+",self.plus),
			("-c",self.del_consequence),
			("-m",self.del_move),
			("-",self.minus),
			("add char",self.add_char),
			("call",self.call),
			("clear",self.clear),
			("del char",self.del_char),
			("new game",self.new_game),
			("raise",self.raise_dice),
			("rename char",self.rename_char),
			("roll",self.roll),
			("set char",self.set_char),
			("view",self.view)
		]

		self.clear_commands = [
			("cpools",self.clear_cpools),
			("dpools",self.clear_dpools),
			("pools",self.clear_pools)
		]

		self.view_commands = [
			("chars",self.view_characters),
			("characters",self.view_characters),
			("cpool",self.view_cpool),
			("dpools",self.view_dpools),
			("dpool",self.view_dpool),
			("moves",self.view_moves),
			("sheet",self.view_sheet),
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
			"moves (char_id text, character_id int, dice text, name text, used int)",
			"consequences (char_id text, character_id int, dice text, name text)"
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

	def get_next_char_id(self, table="characters", character_id=None):
		chars = string.ascii_uppercase+string.ascii_lowercase

		if table == "characters":
			cur = self.db.execute("SELECT char_id FROM characters WHERE active = 1 ORDER BY char_id")
		if table == "consequences":
			cur = self.db.execute("SELECT char_id FROM consequences WHERE character_id = ? ORDER BY char_id", [character_id])
		if table == "moves":
			cur = self.db.execute("SELECT char_id FROM moves WHERE character_id = ? ORDER BY char_id", [character_id])
		
		char_ids = [c[0] for c in cur.fetchall()]
		cur.close()
		
		for char in chars:
			if char not in char_ids:
				return char
		
		raise FeedbackError("Too many active characters!")


	def get_player_char(self,pid):
		c = next((char for char in self.characters if char.player and int(char.player) == int(pid)),None)

		if c:
			return c

		raise FeedbackError("Set your character first! (`dq set char [their name]`)")


	def parse_dice(self, dice):
		try:
			amt, die = dice.split('d')
			amt = int(amt)
			die = int(die)
			if amt < 1 or die < 1:
				raise
		except Exception as e:
			raise FeedbackError("Invalid roll!")

		return amt, die


	def select_char(self,indicator):
		if len(indicator) == 1:
			return next((char for char in self.characters if char.char_id == indicator), None)
		else:
			return next((char for char in self.characters if char.name.lower().startswith(indicator.lower())), None)

		raise FeedbackError("Couldn't find that character")

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
			elif m.content.lower().startswith('n') and self.confirming:
				await self.deny(m)

		except FeedbackError as e:
			await m.reply(f"Hold up: {e}", mention_author=False)

		except Exception as e:
			self.log(traceback.format_exc())
			await m.reply(f"ERROR: {e}", mention_author=False)


	# COMMAND PARSING

	async def parse_command(self,m):
		for command,method in self.commands:
			if m.content[3:].startswith(command):
				await method(m)
				return

	async def view(self,m):
		for command,method in self.view_commands:
			if m.content[8:] == command:
				await method(m)
				return
		await self.view_char(m)

	# assuming del char only for these two
	async def confirm(self,m):
		if m.author.id != self.confirming[1]:
			return
		self.confirming[0]()
		self.confirming = None
		await m.reply("Okay, done!", mention_author=False)

	async def deny(self,m):
		if m.author.id != self.confirming[1]:
			return
		self.confirming = None
		await m.reply("Okay, nevermind!", mention_author=False)

	async def clear(self,m):
		for command,method in self.clear_commands:
			if m.content[9:] == command:
				await method(m)
				return
		raise FeedbackError("Clear what? (dpools/cpools/pools)")

	# +
	# -rolls x y-sided dice and adds results to your character's dice pool
	# -or add n to your character's dice pool
	# -or rolls the indicated move and adds it to the character’s dice pool
	async def plus(self,m):
		d = None
		try:
			d = self.parse_dice(m.content[5:])
		except FeedbackError:
			pass

		if d:
			await self.plus_dice(m,d)
			return

		try:
			d = int(m.content[5:])
		except:
			pass

		if d:
			await self.plus_int(m,d)
			return

		await self.plus_move(m)

	# dice
	# cs = all consequences
	# indicated move
	async def roll(self,m):
		if m.content[8:] == 'cs':
			await self.roll_consequences(m)
			return

		d = None
		try:
			d = self.parse_dice(m.content[8:])
		except FeedbackError:
			pass
		
		if d:
			await self.roll_dice(m,d)
			return

		await self.roll_move(m)


	# RESPONSE FORMATTING
	
	# select active chars + print them in order of char_id
	@property
	def char_list(self):
		return "\n".join([f"   {c.char_id} - {c.name}" for c in self.characters])

	# COMMANDS

	async def add_char(self,m):
		name = m.content[12:]
		char = Character(self, name)
		await m.reply(f"Added {name} ({char.char_id}) to the game!\n\n```js\n_\nCharacters:\n{self.char_list}\n```", mention_author=False)


	async def add_consequence(self,m):
		char = self.get_player_char(m.author.id)
		char.add_consequence(m.content[6:])
		await m.reply(f"Added!\n\n{char.print_list(char.consequence_list,'Consequences')}", mention_author=False)


	async def add_move(self,m):
		char = self.get_player_char(m.author.id)
		char.add_move(m.content[6:])
		await m.reply(f"Added!\n\n{char.print_list(char.move_list,'Moves')}", mention_author=False)

	# needs vals in dice pool
	async def call(self,m):
		await m.reply("calling with n...")
		pass


	async def clear_cpools(self,m):
		for c in self.characters:
			c.clear_consequences()
		await m.reply("Cleared all consequence pools!", mention_author=False)


	# needs vals in dice pool
	async def clear_dpools(self,m):
		await m.reply("clearing dpools...")
		pass


	# needs vals in dice pool
	async def clear_pools(self,m):
		await m.reply("clearing pools...")
		pass


	async def del_char(self,m):
		char = self.get_player_char(m.author.id)
		self.confirming = (char.archive,m.author.id)

		await m.reply(f"Deleting {char.name}. Are you sure? (Y/n)", mention_author=False)


	async def del_consequence(self,m):
		char = self.get_player_char(m.author.id)
		char.del_consequence(m.content[6:])
		await m.reply(f"Deleted consequence!\n{char.print_list(char.consequence_list,'Consequences')}", mention_author=False)


	async def del_move(self,m):
		await m.reply("deleting move...")
		pass


	async def minus(self,m):
		await m.reply("removing vals from dpool...")
		pass


	async def new_game(self,m):
		await m.reply("starting new game with new chars...")
		pass


	async def plus_dice(self,m,dice):
		await m.reply("rolling dice and adding results to dpool...")
		pass


	async def plus_int(self,m,n):
		await m.reply("adding value to dpool...")
		pass


	async def plus_move(self,m):
		await m.reply("rolling move and adding results to dpool...")
		pass


	async def raise_dice(self,m):
		await m.reply("raising with n...")
		pass


	async def roll_consequences(self,m):
		await m.reply("rolling all consequences...")
		pass


	async def roll_dice(self,m,d):
		amt, die = d

		rolls = [random.randint(1,die) for i in range(amt)]
		rolls = sorted(rolls, key=lambda x: 0-x)
		total = sum(rolls)
		rlist = ' + '.join([str(r) for r in rolls])

		reply = f"{total} = {rlist}" if len(rolls) > 1 else total
		reply = f"Rolled {amt}d{die}:\n`{reply}`"

		await m.reply(reply, mention_author=False)


	async def roll_move(self,m):
		await m.reply("rolling a move...")
		pass


	async def rename_char(self,m):
		await m.reply("renaming a character...")
		pass


	async def set_char(self,m):
		char = self.select_char(m.content[12:])
		char.player = m.author.id

		reply = f"You are now playing as {char.name}.\n\n"
		reply += char.sheet

		await m.reply(reply, mention_author=False)


	async def view_characters(self,m):
		await m.reply(f"```js\n_\nCharacters:\n{self.char_list}\n```", mention_author=False)


	async def view_char(self,m):
		await m.reply("viewing a character...")
		pass


	async def view_cpool(self,m):
		await m.reply("viewing your cpool...")
		pass


	async def view_dpool(self,m):
		await m.reply("viewing your dpool...")
		pass


	async def view_dpools(self,m):
		await m.reply("viewing all dpools...")
		pass


	async def view_moves(self,m):
		await m.reply("viewing your moves...")
		pass


	async def view_sheet(self,m):
		await m.reply("viewing your sheet...")
		pass

