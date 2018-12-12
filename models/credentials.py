from google.appengine.ext import db
from oauth2client.contrib.appengine import CredentialsProperty

class TokenizedCredentialsModel(db.Model):
	credentials = CredentialsProperty()