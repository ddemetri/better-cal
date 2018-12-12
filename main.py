import webapp2

from oauth import decorator
from handlers import setup
from handlers import calendar
from handlers import contacts


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
	webapp2.Route('/calendars/ical/v1', handler=calendar.CalendarHandler, name='ical'),
	webapp2.Route('/contacts/birthday/delete', handler=contacts.DeleteBirthday, name='delete_birthday'),
	webapp2.Route('/contacts/contact/delete', handler=contacts.DeleteContact, name='delete_contact'),
	webapp2.Route('/account/delete', handler=DeleteAccount, name='delete_account'),
	webapp2.Route(decorator.callback_path, handler=decorator.callback_handler(), name='oauth')
], debug=True)