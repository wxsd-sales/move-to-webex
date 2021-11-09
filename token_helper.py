import json
import traceback
import tornado.gen

from settings import Settings

from datetime import datetime, timedelta
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError


class User(object):
    def __init__(self, person_id, access_token, refresh_token):
        self.person_id = person_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.refresh_datetime = datetime.now()

    def set_access_token(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_datetime = datetime.now()


class TokenHelper(object):
    def __init__(self):
        self.users = {}
        """
        You can uncomment the 3 lines of code below, and edit the values to be
        a real personId, accessToken and refreshToken for the configured integration.
        This will 'test' refreshing the token immediately on app start, since you would
        otherwise have to wait max_token_age_days to see the refresh.
        """

        #user = User('SOME_PERSON_ID', 'SOME_ACCESS_TOKEN', 'SOME_REFRESH_TOKEN'
        #user.refresh_datetime = datetime.now() - timedelta(days=2)
        #self.users.update({user.person_id : user})

    def update_user(self, person_id, access_token, refresh_token):
        self.users.update({ person_id : User(person_id, access_token, refresh_token) })

    @tornado.gen.coroutine
    def refresh_token(self, user):
        access_token = None
        try:
            print("TokenHelper.refresh_token:{0}".format(user.refresh_token))
            headers = {'accept':'application/json', 'content-type':'application/x-www-form-urlencoded'}
            payload = ("grant_type=refresh_token&client_id={0}&client_secret={1}&"
                        "refresh_token={2}").format(Settings.client_id, Settings.client_secret, user.refresh_token)
            url = "https://webexapis.com/v1/access_token"
            request = HTTPRequest(url, method="POST", headers=headers, body=payload, request_timeout=40)
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch(request)
            result = json.loads(response.body.decode("utf-8"))
            access_token = result.get("access_token")
            user.set_access_token(access_token)
            print("TokenHelper.refresh_token - New access token for user.person_id:{0}".format(user.person_id))
            print("TokenHelper.refresh_token - access_token:{0}".format(access_token))
        except HTTPError as he:
            print("TokenHelper.refresh_token HTTPError:{0}".format(he.response.body))
            traceback.print_exc()
        except Exception as e:
            print("TokenHelper.refresh_token Exception:{0}".format(e))
            traceback.print_exc()
        if access_token == None:
            print("TokenHelper.refresh_token - An error occurred attempting to refresh the token for user.person_id:{0}".format(user.person_id))
        raise tornado.gen.Return(access_token)


    @tornado.gen.coroutine
    def event_loop(self):
        while True:
            print("TokenHelper.event_loop - checking for old tokens")
            try:
                now = datetime.now()
                x_days_ago = now - timedelta(days=Settings.max_token_age_days)
                for person_id in self.users:
                    if self.users[person_id].refresh_datetime < x_days_ago:
                        yield self.refresh_token(self.users[person_id])
            except Exception as e:
                traceback.print_exc()
            print("TokenHelper.event_loop - done. Sleeping for {0} seconds.".format(Settings.loop_interval_sleep_seconds))
            yield tornado.gen.sleep(Settings.loop_interval_sleep_seconds)
