import os

from oauth2client.contrib.appengine import OAuth2DecoratorFromClientSecrets

decorator = OAuth2DecoratorFromClientSecrets(
	filename=os.path.join(os.path.dirname(__file__), 'oauth_secrets.json'),
	scope=[
		'https://www.googleapis.com/auth/userinfo.profile',
		'https://www.googleapis.com/auth/userinfo.email',
		'https://www.googleapis.com/auth/contacts',
		'https://www.googleapis.com/auth/calendar'
	])