import os
import json
import hashlib

from httplib2 import Http
from googleapiclient.discovery import build
from oauth2client.contrib.appengine import StorageByKeyName

from models.credentials import TokenizedCredentialsModel


class TokenGenerator:
	def __init__(self, credentials, user_id):
		self.credentials = credentials
		self.user_id = user_id

	def get_token(self):
		secrets_filepath = os.path.join(os.path.dirname(__file__), 'urltoken_secrets.json')
		with open(secrets_filepath, 'r') as fp:
			secrets = json.load(fp)
		token = hashlib.sha256(self.user_id.encode() + secrets.get('hash_seed').encode()).hexdigest()

		if (self.credentials.refresh_token):
			storage = StorageByKeyName(TokenizedCredentialsModel, token, 'credentials')
			storage.put(self.credentials)

		return token

class TokenProcessor:
	def __init__(self, token):
		self.token = token

	def get_credentials(self):
		storage = StorageByKeyName(TokenizedCredentialsModel, self.token, 'credentials')
		return storage.get()