import os
from dotenv import load_dotenv

load_dotenv()

class Settings(object):
	port = int(os.environ.get("MY_APP_PORT"))

	fedramp_client_id = os.environ.get("MY_FEDRAMP_CLIENT_ID")
	fedramp_client_secret = os.environ.get("MY_FEDRAMP_SECRET")
	
	webex_client_id = os.environ.get("MY_WEBEX_CLIENT_ID")
	webex_client_secret = os.environ.get("MY_WEBEX_SECRET")
	webex_redirect_uri = os.environ.get("MY_WEBEX_REDIRECT_URI")
	webex_scopes = os.environ.get("MY_WEBEX_SCOPES")

	zoom_client_id = os.environ.get("MY_ZOOM_CLIENT_ID")
	zoom_client_secret = os.environ.get("MY_ZOOM_SECRET")
	zoom_redirect_uri = os.environ.get("MY_ZOOM_REDIRECT_URI")

	azure_client_id = os.environ.get("MY_AZURE_CLIENT_ID")
	azure_client_secret = os.environ.get("MY_AZURE_SECRET")
	azure_redirect_uri = os.environ.get("MY_AZURE_REDIRECT_URI")
	azure_scopes = os.environ.get("MY_AZURE_SCOPES")

	mongo_uri = os.environ.get("MY_MONGO_URI")
	mongo_db = os.environ.get("MY_MONGO_DB")
