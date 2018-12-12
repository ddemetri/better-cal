import os
import json
import hashlib


class TokenGenerator:
	def __init__(self, user_id):
		self.user_id = user_id

	def get_token(self):
		secrets_filepath = os.path.join(os.path.dirname(__file__), 'token_secrets.json')
		with open(secrets_filepath, 'r') as fp:
			secrets = json.load(fp)
		print(secrets)
		return hashlib.sha256(self.user_id.encode() + secrets.get('hash_seed').encode()).hexdigest()