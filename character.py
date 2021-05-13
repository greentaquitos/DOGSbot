
from exceptions import FeedbackError

class Character():
	def __init__(self,bot,name=None,db_id=None):
		self.bot = bot
		self._name = name
		self._char_id = None
		self._player_id = None
		self.db_id = db_id 
		if not db_id:
			self.init_record()

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self,v):
		self._name = v

	@property
	def char_id(self):
		if not self._char_id:
			if self.db_id:
				cur = self.bot.db.execute("SELECT char_id FROM characters WHERE rowid = ?",[self.db_id])
				self._char_id = cur.fetchone()[0]
				cur.close()
			else:
				self._char_id = self.bot.get_next_char_id()
		return self._char_id

	@char_id.setter
	def char_id(self,v):
		self._char_id = v

	@property
	def moves(self):
		cur = self.bot.db.execute("SELECT char_id,dice,name,used,rowid FROM moves WHERE character_id = ? ORDER BY char_id",[self.db_id])
		moves = cur.fetchall()
		cur.close()
		return moves

	@property
	def consequences(self):
		cur = self.bot.db.execute("SELECT char_id,dice,name,rowid FROM consequences WHERE character_id = ? ORDER BY char_id",[self.db_id])
		cqs = cur.fetchall()
		cur.close()
		return cqs

	@property
	def player(self):
		cur = self.bot.db.execute("SELECT player_id FROM characters WHERE rowid = ?",[self.db_id])
		pid = cur.fetchone()[0]
		cur.close()
		return pid


	@player.setter
	def player(self,v):
		# unset player if set
		cur = self.bot.db.execute("UPDATE characters SET player_id = '' WHERE player_id = ?",[v])
		cur.execute("UPDATE characters SET player_id = ? WHERE rowid = ?",[v,self.db_id])
		self.bot.db.commit()
		cur.close()

	@property
	def sheet(self):
		return '\n'.join([
			"```js",
			self.name,
			'',
			"DicePool:",
			self.dice_list,
			'',
			"Moves:",
			self.move_list,
			'',
			"Consequences:",
			self.consequence_list,
			"```"
		])

		# select active chars + print them in order of char_id
	@property
	def move_list(self):
		return "\n".join(
			[f"   {c[0]} - {c[1]} - {c[2]}" for c in self.moves if c[3] == 0] + 
			[f"// {c[0]} - {c[1]} - {c[2]}" for c in self.moves if c[3] == 1]
		) if len(self.moves) else "   [empty]"

		# select active chars + print them in order of char_id
	@property
	def consequence_list(self):
		return "\n".join([f"   {c[0]} - {c[1]} - {c[2]}" for c in self.consequences]) if len(self.consequences) else "   [empty]"

	@property
	def dice_list(self):
		cur = self.bot.db.execute("SELECT dice_pool FROM characters WHERE rowid = ?",[self.db_id])
		dice = cur.fetchone()[0]
		dice = '   ' + ", ".join(dice.split(' ')) if dice else "   [empty]"
		cur.close()
		return dice


	def init_record(self):
		cursor = self.bot.db.cursor()
		cursor.execute("INSERT INTO characters (name,active,char_id) VALUES (?,?,?)", [self.name, 1, self.char_id])
		self.bot.db.commit()
		i = cursor.lastrowid
		cursor.close()
		self.db_id = i


	def add_consequence(self,c):
		dice = 'd'.join(str(d) for d in self.bot.parse_dice(c.split(' ')[0]))
		c = c[c.index(' ')+1:] if len(c.split(' ')) > 1 else ''
		char_id = self.bot.get_next_char_id('consequences', self.db_id)

		cursor = self.bot.db.cursor()
		cursor.execute("INSERT INTO consequences(name, dice, char_id, character_id) VALUES (?,?,?,?)", [c, dice, char_id, self.db_id])
		self.bot.db.commit()
		cursor.close()

	def add_move(self,c):
		dice = 'd'.join(str(d) for d in self.bot.parse_dice(c.split(' ')[0]))
		
		if not len(c.split(' ')) > 1:
			raise FeedbackError("You must include a label for your move! eg, `dq +m 2d6 Body`")
		c = c[c.index(' ')+1:]
		
		char_id = self.bot.get_next_char_id('moves', self.db_id)

		cursor = self.bot.db.cursor()
		cursor.execute("INSERT INTO moves(name, dice, char_id, character_id, used) VALUES (?,?,?,?,0)", [c, dice, char_id, self.db_id])
		self.bot.db.commit()
		cursor.close()

	def clear_consequences(self):
		cursor = self.bot.db.cursor()
		cursor.execute("DELETE FROM consequences WHERE character_id = ?",[self.db_id])
		self.bot.db.commit()
		cursor.close()

	def archive(self):
		cursor = self.bot.db.cursor()
		cursor.execute("UPDATE characters SET active = 0 WHERE rowid = ?",[self.db_id])
		self.bot.db.commit()
		cursor.close()

	def del_consequence(self,c):
		consequence = self.select_consequence(c)
		cursor = self.bot.db.cursor()
		cursor.execute("DELETE FROM consequences WHERE rowid = ?",[consequence[3]])
		self.bot.db.commit()
		cursor.close()

	def select_consequence(self,c):
		if len(c) == 1:
			return next((con for con in self.consequences if con[0] == c), None)
		else:
			return next((con for con in self.consequences if con[2].lower().startswith(c.lower())), None)

		raise FeedbackError("Couldn't find that consequence")

	def print_list(self,l,title):
		return f"```js\n{self.name}\n\n{title}:\n{l}\n```"

