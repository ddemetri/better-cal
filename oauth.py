import logging
import os

from oauth2client.contrib.appengine import OAuth2DecoratorFromClientSecrets

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
	# Production
	logging.info('Using production oauth credentials')
	secrets_filename = 'secrets/oauth.json'
else:
	# Dev
	logging.info('Using dev oauth credentials')
	secrets_filename = 'secrets/dev_oauth.json'

decorator = OAuth2DecoratorFromClientSecrets(
	filename=os.path.join(os.path.dirname(__file__), secrets_filename),
	scope=[
		'https://www.googleapis.com/auth/userinfo.profile',
		'https://www.googleapis.com/auth/userinfo.email',
		'https://www.googleapis.com/auth/contacts',
		'https://www.googleapis.com/auth/calendar'
	])