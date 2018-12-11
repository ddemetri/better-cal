import pprint
import datetime
import hashlib
import jinja2
import json
import os
import webapp2

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.contrib.appengine import CredentialsProperty
from oauth2client.contrib.appengine import OAuth2Decorator
from oauth2client.contrib.appengine import StorageByKeyName


# OAuth for access to Google Contacts
CLIENT_ID = '157789339648-2jfkaq0c533rn8jldb0luekfm2ddi8ju.apps.googleusercontent.com'
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/calendar'
]
OAUTH_DECORATOR = OAuth2Decorator(
 client_id=CLIENT_ID,
 client_secret=CLIENT_SECRET,
 scope=SCOPES)

class UserModel(ndb.Model):
	user = ndb.JsonProperty()

class TokenizedCredentialsModel(db.Model):
	credentials = CredentialsProperty()



def get_connections(credentials):
	service = build('people', 'v1', http=credentials.authorize(Http()))
	method = service.people().connections()

	request = method.list(
		resourceName='people/me',
		pageSize=1000,
		personFields='names,birthdays,phoneNumbers,emailAddresses')
	connections = []
	while request is not None:
		response = request.execute()
		connections = connections + response.get('connections', [])
		request = method.list_next(request, response)

	return connections

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

class Setup(webapp2.RequestHandler):
	@OAUTH_DECORATOR.oauth_required
	def get(self):
		credentials = OAUTH_DECORATOR.get_credentials()

		user_info_service = build(serviceName='oauth2', version='v2',
								  http=credentials.authorize(Http()))
		user_info = user_info_service.userinfo().get().execute()
		user_id = user_info.get('id')

		hashed_user_id = hashlib.sha256(user_id.encode() + HASH_SEED).hexdigest()

		# Update tokenized oauth credentials
		if (credentials.refresh_token):
			storage = StorageByKeyName(TokenizedCredentialsModel, hashed_user_id, 'credentials')
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
										  token=hashed_user_id,
										  _full=True),
			'token': hashed_user_id,
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

		HTML_JINJA_ENVIRONMENT = jinja2.Environment(
		    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
		    extensions=['jinja2.ext.autoescape'],
		    autoescape=True)
		template = HTML_JINJA_ENVIRONMENT.get_template('setup.html')
		self.response.write(template.render(template_values))


class BirthdaysICalendar(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/calendar'

		# Get credentials from token
		token = self.request.get('token')
		storage = StorageByKeyName(TokenizedCredentialsModel, token, 'credentials')
		credentials = storage.get()

		# Setup template values
		ISO_DATETIME_FORMAT = '{0:%Y}{0:%m}{0:%d}T{0:%H}{0:%M}{0:%S}Z'
		template_values = {
			'connections': [],
			'now': ISO_DATETIME_FORMAT.format(datetime.datetime.utcnow())
		}
		for person in get_connections(credentials):
			birthday = get_birthday(person)
			name = get_primary(person, 'names', 'displayName')
			if not name or not birthday:
				continue

			ICAL_DATE_FORMAT = '{0:%Y}{0:%m}{0:%d}'
			template_values['connections'].append({
				'name': name,
				'possessive': '\'' if name.endswith('s') else '\'s',
				'birthday_date': ICAL_DATE_FORMAT.format(birthday),
				'birthday_month': '{0:%m}'.format(birthday),
				'birthday_day': '{0:%d}'.format(birthday),
				'day_after_birthday': ICAL_DATE_FORMAT.format(birthday + datetime.timedelta(days=1)),
				'phone': get_primary(person, 'phoneNumbers'),
				'email': get_primary(person, 'emailAddresses'),
				'delete_birthday_url': self.uri_for('delete_birthday',
													personId=person.get('resourceName'),
											  		token=token,
											  		_full=True),
				'id': person.get('resourceName')
				})
			
			
		# Output calendar
		ICAL_JINJA_ENVIRONMENT = jinja2.Environment(
			loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
			newline_sequence='\r\n')
		template = ICAL_JINJA_ENVIRONMENT.get_template('birthdays.ical')
		output = template.render(template_values)
		self.response.write(output)

class DeleteBirthday(webapp2.RequestHandler):
	def get(self):

		# Get credentials
		token = self.request.get('token')
		storage = TokenizedCredentialsModel(CredentialsModel, token, 'credentials')
		credentials = storage.get()

		service = build('people', 'v1', http=credentials.authorize(Http()))

		person = service.people().get(
			resourceName=self.request.get('personId'),
			personFields='birthdays',
		).execute()

		person['birthdays'] = []

		request = service.people().updateContact(
			resourceName=self.request.get('personId'),
			updatePersonFields='birthdays',
			body=person
		)
		request.execute()

		self.response.write("Birthday deleted from contact")

class DeleteContact(webapp2.RequestHandler):
	def get(self):

		# Get credentials
		token = self.request.get('token')
		storage = TokenizedCredentialsModel(CredentialsModel, token, 'credentials')
		credentials = storage.get()

		service = build('people', 'v1', http=credentials.authorize(Http()))

		request = service.people().deleteContact(
			resourceName=self.request.get('personId'),
		)
		request.execute()

		self.response.write("Contact deleted")

class DeleteAccount(webapp2.RequestHandler):
	@OAUTH_DECORATOR.oauth_required
	def get(self):
		# TODO(finish implmenetation!)
		# Get credentials
		token = self.request.get('token')
		storage = TokenizedCredentialsModel(CredentialsModel, token, 'credentials')
		credentials = storage.get()

		credentials.revoke()

		self.response.write("Credentials revoked")


app = webapp2.WSGIApplication([
	webapp2.Route('/', handler=Setup, name='home'),
	webapp2.Route('/setup', handler=Setup, name='setup'),
	webapp2.Route('/birthdays/ical/v1', handler=BirthdaysICalendar, name='bday_ical'),
	webapp2.Route('/services/birthday/delete', handler=DeleteBirthday, name='delete_birthday'),
	webapp2.Route('/services/contact/delete', handler=DeleteContact, name='delete_contact'),
	webapp2.Route('/account/delete', handler=DeleteAccount, name='delete_account'),
	(OAUTH_DECORATOR.callback_path, OAUTH_DECORATOR.callback_handler())
], debug=True)