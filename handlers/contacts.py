import webapp2

from googleapiclient.discovery import build
from httplib2 import Http

from urltoken import TokenProcessor


class DeleteBirthday(webapp2.RequestHandler):
	def get(self):
		token = self.request.get('token')
		credentials = TokenProcessor(token).get_credentials()

		service = build('people', 'v1', http=credentials.authorize(Http()))

		contact = (service
					.people()
					.get(resourceName=self.request.get('personId'),
						 personFields='birthdays')
					.execute())
		contact['birthdays'] = []

		(service
			.people()
			.updateContact(
				resourceName=self.request.get('personId'),
				updatePersonFields='birthdays',
				body=contact)
			.execute())

		self.response.write("Birthday deleted from contact")

class DeleteContact(webapp2.RequestHandler):
	def get(self):
		token = self.request.get('token')
		credentials = TokenProcessor(token).get_credentials()

		service = build('people', 'v1', http=credentials.authorize(Http()))

		(service
			.people()
			.deleteContact(resourceName=self.request.get('personId'))
			.execute())

		self.response.write("Contact deleted")