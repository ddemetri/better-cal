import datetime

from googleapiclient.discovery import build
from httplib2 import Http

def get_connections(credentials):
	service = build('people', 'v1', http=credentials.authorize(Http()))
	method = service.people().connections()

	request = method.list(
		resourceName='people/me',
		pageSize=1000,
		sortOrder='LAST_NAME_ASCENDING',
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
		date = birthday.get('date', {})
		if (source_type == 'CONTACT' and date.get('month') and date.get('day')):
			return datetime.date(int(date.get('year', 1900)),
								 int(date.get('month')),
								 int(date.get('day')))

def get_primary(person, collection_name, attr='value'):
	list = person.get(collection_name, [])
	for item in list:
		if item.get('metadata', {}).get('primary'):
			return item.get(attr)