
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
				self.bot.log("getting char id w db id: "+str(self.db_id))
				cur = self.bot.db.execute("SELECT char_id FROM characters WHERE rowid = ?",[self.db_id])
				self._char_id = cur.fetchone()[0]
				cur.close()
			else:
				self._char_id = self.bot.get_next_char_id()
		return self._char_id

	@char_id.setter
	def char_id(self,v):
		self._char_id = v

	def init_record(self):
		cursor = self.bot.db.cursor()
		cursor.execute("INSERT INTO characters (name,active,char_id) VALUES (?,?,?)", [self.name, 1, self.char_id])
		self.bot.db.commit()
		i = cursor.lastrowid
		cursor.close()
		self.db_id = i