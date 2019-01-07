import datetime
import webapp2

from oauth2client.client import HttpAccessTokenRefreshError

from connections import get_connections
from connections import get_birthday
from connections import get_primary
from templates.template import ical_jinja_environment
from urltoken import TokenProcessor

class CalendarHandler(webapp2.RequestHandler):
	def get(self):
		if not set(self.request.arguments()).isdisjoint(['nocache', 'noCache', 'fake']):
			self.response.set_status(404)
			return

		token = self.request.get('token')
		credentials = TokenProcessor(token).get_credentials()
		if not credentials:
			self.response.set_status(404)
			return

		# Setup template values
		try:
			connections = get_connections(credentials)
		except HttpAccessTokenRefreshError as err:
			self.response.headers['Content-Type'] = 'text/calendar'
			template = ical_jinja_environment.get_template('birthdays_error.ical')
			output = template.render()
			self.response.write(output)
			return

		ISO_DATETIME_FORMAT = '{0:%Y}{0:%m}{0:%d}T{0:%H}{0:%M}{0:%S}Z'
		template_values = {
			'connections': [],
			'now': ISO_DATETIME_FORMAT.format(datetime.datetime.utcnow())
		}
		for person in connections:
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
		self.response.headers['Content-Type'] = 'text/calendar'
		template = ical_jinja_environment.get_template('birthdays.ical')
		output = template.render(template_values)
		self.response.write(output)