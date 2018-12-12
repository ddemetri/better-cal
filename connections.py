from googleapiclient.discovery import build
from httplib2 import Http

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