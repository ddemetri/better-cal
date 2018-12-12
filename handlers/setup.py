import datetime
import webapp2
import pprint

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.contrib.appengine import CredentialsProperty
from oauth2client.contrib.appengine import StorageByKeyName

from connections import get_connections
from template import html_jinja_environment
from oauth import decorator
from urltoken import TokenGenerator
from models.credentials import TokenizedCredentialsModel
from models.users import UserModel

def get_birthday(person):
	birthdays = person.get('birthdays', [])
	for birthday in birthdays:
		source_type = birthday.get('metadata', {}).get('source', {}).get('type')
		if (source_type == 'CONTACT'):
			date = birthday.get('date', {})
			return datetime.date(int(date.get('year', 1900)),
								 int(date.get('month')),
								 int(date.get('day')))

def get_primary(person, collection_name, attr='value'):
	list = person.get(collection_name, [])
	for item in list:
		if item.get('metadata', {}).get('primary'):
			return item.get(attr)

class SetupHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		super(SetupHandler, self).__init__(request, response)
		self.template = html_jinja_environment.get_template('setup.html')

	@decorator.oauth_required
	def get(self):
		credentials = decorator.get_credentials()

		user_info_service = build(serviceName='oauth2', version='v2',
								  http=credentials.authorize(Http()))
		user_info = user_info_service.userinfo().get().execute()
		user_id = user_info.get('id')


		token_generator = TokenGenerator(user_id)
		token = token_generator.get_token()
		
		# Update tokenized oauth credentials
		if (credentials.refresh_token):
			storage = StorageByKeyName(TokenizedCredentialsModel, token, 'credentials')
			storage.put(credentials)
		
		# Update user info		
		UserModel(key=ndb.Key(UserModel, user_id), user=user_info).put()

		# Remove Google's "Birthdays" calendar
		DEFAULT_BIRTHDAYS_CALENDAR_ID = 'addressbook#contacts@group.v.calendar.google.com'
		calendarService = build('calendar', 'v3', http=credentials.authorize(Http()))
		calList = calendarService.calendarList().list().execute()
		if any(cal for cal in calList.get('items') if cal.get('id') == DEFAULT_BIRTHDAYS_CALENDAR_ID):
			calendarService.calendarList().delete(
				calendarId=DEFAULT_BIRTHDAYS_CALENDAR_ID
			).execute()
		
		# Output website
		template_values = {
			'bday_ical_url': self.uri_for('bday_ical',
										  token=token,
										  _full=True),
			'token': token,
			'connections': [],
		}
		for person in get_connections(credentials):
			birthday = get_birthday(person)
			name = get_primary(person, 'names', 'displayName')
			if not name or not birthday:
				continue

			template_values['connections'].append({
				'name': name,
				'email': get_primary(person, 'emailAddresses'),
				'id': person.get('resourceName')
				})

		self.response.write(self.template.render(template_values))