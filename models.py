from peewee import *
from playhouse.sqlite_ext import AutoIncrementField
from datetime import datetime

database_proxy = DatabaseProxy()



class BufferContextManager():
	def __init__(self, model):
		self.model = model
		self.buffer = []

	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		self.execute()
		
	def insert(self, **kwargs):
		result = None
		if len(self.buffer) == 999:
			result = self.execute()

		self.buffer.append(kwargs)
		
		return result

	def execute(self):
		if len(self.buffer):
			last_id = self.model.insert_many(self.buffer).execute()
			self.buffer = []
			return last_id

class BaseModel(Model):
	class Meta:
		database = database_proxy



# class SchemaVersions(BaseModel):
# 	class Meta:
# 		table_name = 'SchemaVersions'

# 	SchemaVersionID = AutoIncrementField(primary_key=True)
# 	ScriptName = CharField()
# 	Applied = DateTimeField()

	


class ContentVersion(BaseModel):
	class Meta:
		table_name = 'ContentVersion'

	Id = AutoIncrementField(primary_key=True)
	EngineVersion = TextField()
	ForkId = TextField()
	ForkVersion = TextField()
	Hash = BlobField(null=True, default=None)
	ZipHash = BlobField(null=True, default=None)
	LastUsed = DateField(default=datetime.now().date)

	@classmethod
	def buffer(cls):
		return BufferContextManager(cls)

	@property
	def content_manifest(self):
		return ContentManifest.select().where(ContentManifest.VersionId == self.Id)
		

class Content(BaseModel):
	class Meta:
		table_name = 'Content'

	Id = AutoIncrementField(primary_key=True)
	Hash = BlobField()
	Size = IntegerField(default=None, null=True)
	Compression = IntegerField(default=0)
	Data = BlobField(default=None, null=True)

	@classmethod
	def buffer(cls):
		return BufferContextManager(cls)
	
class ContentManifest(BaseModel):
	class Meta:
		table_name = 'ContentManifest'

	Id = AutoIncrementField(primary_key=True)
	VersionId = IntegerField()
	Path = TextField()
	ContentId = IntegerField()

	@classmethod
	def buffer(cls):
		return BufferContextManager(cls)
	
	@property
	def content(self):
		return Content.select().where(Content.Id == self.ContentId).get_or_none()


class DatabseInfo(BaseModel):
	class Meta:
		table_name = 'databse_info'

	Id = AutoIncrementField(primary_key=True)
	Created = DateTimeField()
	



# class ContentEngineDependency(BaseModel):
# 	class Meta:
# 		table_name = 'ContentEngineDependency'

# 	Id = AutoIncrementField(primary_key=True)
# 	VersionId = IntegerField()
# 	ModuleName = TextField()
# 	ModuleVersion = TextField()


tables = [
	# SchemaVersions,
	ContentVersion,
	Content,
	ContentManifest,
	# ContentEngineDependency,
	DatabseInfo
]



