from google.appengine.ext import ndb

class UserModel(ndb.Model):
	user = ndb.JsonProperty()