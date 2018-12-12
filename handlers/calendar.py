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

from connections import get_connections
from template import html_jinja_environment

from models.credentials import TokenizedCredentialsModel

class CalendarHandler(webapp2.RequestHandler):
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