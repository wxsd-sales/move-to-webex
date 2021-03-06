import json
import traceback
import urllib.parse

import tornado.gen
import tornado.web

from base64 import b64encode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from handlers.base import BaseHandler

from spark import Spark
from settings import Settings

class WebexOAuthHandler(BaseHandler):

    def build_access_token_payload(self, code, client_id, client_secret, redirect_uri):
        payload = "client_id={0}&".format(client_id)
        payload += "client_secret={0}&".format(client_secret)
        payload += "grant_type=authorization_code&"
        payload += "code={0}&".format(code)
        payload += "redirect_uri={0}".format(redirect_uri)
        return payload

    @tornado.gen.coroutine
    def get_tokens(self, code, state=""):
        print('generating token for state:{0}'.format(state))
        if state == "fedramp":
            url = "https://api-usgov.webex.com/v1/access_token"
            api_url = 'https://api-usgov.webex.com/v1'
            payload = self.build_access_token_payload(code, Settings.fedramp_client_id, Settings.fedramp_client_secret, Settings.webex_redirect_uri)
        else:
            url = "https://webexapis.com/v1/access_token"
            api_url = 'https://webexapis.com/v1'
            payload = self.build_access_token_payload(code, Settings.webex_client_id, Settings.webex_client_secret, Settings.webex_redirect_uri)
        headers = {
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded"
            }
        try:
            request = HTTPRequest(url, method="POST", headers=headers, body=payload)
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch(request)
            resp = json.loads(response.body.decode("utf-8"))
            print("WebexOAuthHandler.get_tokens /access_token Response: {0}".format(resp))
            person = yield Spark(resp["access_token"]).get_with_retries_v2('{0}/people/me'.format(api_url))
            person.body.update({"token":resp["access_token"]})
            print(person.body)
            if state == "fedramp":
                self.set_secure_cookie("MoveToFedRamp-User", json.dumps(person.body), expires_days=1, version=2)
            else:
                self.set_secure_cookie("ZoomToWebex-User", json.dumps(person.body), expires_days=1, version=2)
        except Exception as e:
            print("WebexOAuthHandler.get_tokens Exception:{0}".format(e))
            traceback.print_exc()



    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = "Error"
        try:
            print('Webex OAuth: {0}'.format(self.request.full_url()))
            state = self.get_argument("state","")
            if state == "fedramp":
                person = self.get_fedramp_user()
            else:
                person = self.get_current_user()
            if not person:
                if self.get_argument("code", None):
                    code = self.get_argument("code")
                    yield self.get_tokens(code, state)
                    if state != "":
                        self.redirect(state)
                    else:
                        self.redirect("/")
                    return
                else:
                    authorize_url = '{0}?client_id={1}&response_type=code&redirect_uri={2}&scope={3}&state={4}'
                    if state == "fedramp":
                        use_url = "https://api-usgov.webex.com/v1/authorize"
                        authorize_url = authorize_url.format(use_url, Settings.fedramp_client_id, urllib.parse.quote_plus(Settings.webex_redirect_uri), Settings.webex_scopes, state)
                    else:
                        use_url = 'https://webexapis.com/v1/authorize'
                        authorize_url = authorize_url.format(use_url, Settings.webex_client_id, urllib.parse.quote_plus(Settings.webex_redirect_uri), Settings.webex_scopes, state)
                    print("WebexOAuthHandler.get authorize_url:{0}".format(authorize_url))
                    self.redirect(authorize_url)
                    return
            else:
                print("Already authenticated.")
                if state == "":
                    self.redirect("/")
                else:
                    self.redirect("/{0}".format(state))
                return
        except Exception as e:
            response = "{0}".format(e)
            print("WebexOAuthHandler.get Exception:{0}".format(e))
            traceback.print_exc()
        self.write(response)


class ZoomOAuthHandler(BaseHandler):

    @tornado.gen.coroutine
    def get_tokens(self, code):
        url = "https://zoom.us/oauth/token"
        payload = "grant_type=authorization_code&"
        payload += "code={0}&".format(code)
        payload += "redirect_uri={0}".format(Settings.zoom_redirect_uri)

        #we need to base 64 encode it
        #and then decode it to acsii as python 3 stores it as a byte string
        userAndPass = b64encode("{0}:{1}".format(Settings.zoom_client_id, Settings.zoom_client_secret).encode()).decode("ascii")
        print(userAndPass)
        print(type(userAndPass))

        headers = {
            'authorization': 'Basic {0}'.format(userAndPass),
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded"
            }
        try:
            request = HTTPRequest(url, method="POST", headers=headers, body=payload)
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch(request)
            resp = json.loads(response.body.decode("utf-8"))
            print("ZoomOAuthHandler.get_tokens /access_token Response: {0}".format(resp))
            person = json.loads(self.get_current_user())
            self.application.settings['db'].insert_user(person['id'], resp['access_token'], resp['expires_in'], resp['refresh_token'], "zoom")
        except Exception as e:
            print("ZoomOAuthHandler.get_tokens Exception:{0}".format(e))
            traceback.print_exc()



    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = "Error"
        try:
            print('Zoom OAuth: {0}'.format(self.request.full_url()))
            person = self.get_current_user()
            print(person)
            if person:
                person = json.loads(person)
                if self.application.settings['db'].get_user(person['id'], "zoom") == None:
                    if self.get_argument("code", None):
                        code = self.get_argument("code")
                        yield self.get_tokens(code)
                        state = self.get_argument("state","")
                        if state != "":
                            self.redirect(state)
                        else:
                            self.redirect("/")
                        return
                    else:
                        state = self.get_argument("state","")
                        authorize_url = 'https://zoom.us/oauth/authorize?response_type=code&client_id={0}&redirect_uri={1}&state={2}'.format(Settings.zoom_client_id, urllib.parse.quote_plus(Settings.zoom_redirect_uri), state)
                        print("ZoomOAuthHandler.get authorize_url:{0}".format(authorize_url))
                        self.redirect(authorize_url)
                        return
                else:
                    print("Already Zoom Authenticated.")
                    self.redirect("/")
                    return
            else:
                print("No Webex authentication.")
                self.redirect("/")
                return
        except Exception as e:
            response = "{0}".format(e)
            print("ZoomOAuthHandler.get Exception:{0}".format(e))
            traceback.print_exc()
        self.write(response)


class AzureOAuthHandler(BaseHandler):

    @tornado.gen.coroutine
    def get_tokens(self, code, person):
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        payload = "grant_type=authorization_code&"
        payload += "client_id={0}&".format(Settings.azure_client_id)
        payload += "scope={0}&".format(urllib.parse.unquote(Settings.azure_scopes))
        payload += "code={0}&".format(code)
        payload += "redirect_uri={0}&".format(Settings.azure_redirect_uri)
        payload += "client_secret={0}".format(Settings.azure_client_secret)
        print(payload)
        headers = {
            'content-type': "application/x-www-form-urlencoded"
            }
        try:
            request = HTTPRequest(url, method="POST", headers=headers, body=payload)
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch(request)
            print(response.body)
            resp = json.loads(response.body.decode("utf-8"))
            print("AzureOAuthHandler.get_tokens /access_token Response: {0}".format(resp))
            self.application.settings['db'].insert_user(person['id'], resp['access_token'], resp['expires_in'], resp['refresh_token'], "msft")
        except Exception as e:
            print("AzureOAuthHandler.get_tokens Exception:{0}".format(e))
            traceback.print_exc()



    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = "Error"
        try:
            print('Azure OAuth: {0}'.format(self.request.full_url()))
            state = self.get_argument("state","")
            if state == "fedramp":
                person = self.get_fedramp_user()
            else:
                person = self.get_current_user()
            print(person)
            if person:
                person = json.loads(person)
                if self.application.settings['db'].get_user(person['id'], "msft") == None:
                    if self.get_argument("code", None):
                        code = self.get_argument("code")
                        yield self.get_tokens(code, person)
                        if state != "":
                            self.redirect(state)
                        else:
                            self.redirect("/")
                        return
                    else:
                        state = self.get_argument("state","")
                        authorize_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={0}&response_type=code'.format(Settings.azure_client_id)
                        authorize_url += '&redirect_uri={0}&response_mode=query&scope=offline_access%20{1}&state={2}'.format(urllib.parse.quote_plus(Settings.azure_redirect_uri), Settings.azure_scopes, state)
                        print("AzureOAuthHandler.get authorize_url:{0}".format(authorize_url))
                        self.redirect(authorize_url)
                        return
                else:
                    print("Already Azure Authenticated.")
                    self.redirect("/")
                    return
            else:
                print("No Azure authentication.")
                self.redirect("/")
                return
        except Exception as e:
            response = "{0}".format(e)
            print("AzureOAuthHandler.get Exception:{0}".format(e))
            traceback.print_exc()
        self.write(response)
