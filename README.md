# Better Cal
Hosted at https://better-cal.appspot.com

Better Cal replaces Google's built-in Birthdays calendar with an alternative that gives you full control.

To run for yourself:
- Download and install the Google Cloud SDK
- Download credentials in JSON format for the Google Calendar API and Google People API.
- Move those credentials into `/oauth_secrets.json`.
- Create a file called `/urltoken_secrets.json` with a JSON object having a property called `hash_seed` that is a long, random string.
- Run `bin/install_library`
- Run `dev_appserver.py .`
- Access the application at http://localhost:8080
