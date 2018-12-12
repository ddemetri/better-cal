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
from oauth2client.contrib.appengine import StorageByKeyName

from handlers import setup
from handlers import calendar

from oauth import decorator

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
	# @OAUTH_DECORATOR.oauth_required
	def get(self):
		# TODO(finish implmenetation!)
		# Get credentials
		# 	token = self.request.get('token')
		# 	storage = TokenizedCredentialsModel(CredentialsModel, token, 'credentials')
		# 	credentials = storage.get()

		# 	credentials.revoke()

		self.response.write("Credentials revoked")


app = webapp2.WSGIApplication([
	webapp2.Route('/', handler=setup.SetupHandler, name='home'),
	webapp2.Route('/setup', handler=setup.SetupHandler, name='setup'),
	webapp2.Route('/birthdays/ical/v1', handler=calendar.CalendarHandler, name='bday_ical'),
	webapp2.Route('/services/birthday/delete', handler=DeleteBirthday, name='delete_birthday'),
	webapp2.Route('/services/contact/delete', handler=DeleteContact, name='delete_contact'),
	webapp2.Route('/account/delete', handler=DeleteAccount, name='delete_account'),
	webapp2.Route(decorator.callback_path, handler=decorator.callback_handler(), name='oauth')
], debug=True)