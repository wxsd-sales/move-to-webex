import json
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        cookie = self.get_secure_cookie("ZoomToWebex-User", max_age_days=1, min_version=2)
        return cookie
    
    def get_fedramp_user(self):
        cookie = self.get_secure_cookie("MoveToFedRamp-User", max_age_days=1, min_version=2)
        return cookie

    def load_page(self, page="main", msft_token=True, zoom_token=True, meetings_count=None):
        redirect_to = ""
        if page != "main":
            redirect_to += "?state={0}".format(page)
        if page == "fedramp":
            person = self.get_fedramp_user()
        else:
            person = self.get_current_user()
        if not person:
            self.redirect('/webex-oauth{0}'.format(redirect_to))
        else:
            person = json.loads(person)
            print(person)
            tokens = {}
            if msft_token:
                tokens.update({"msft_token": self.application.settings['db'].is_user(person['id'], "msft") })
            if zoom_token:
                tokens.update({"zoom_token": self.application.settings['db'].is_user(person['id'], "zoom") })
            self.render("{0}.html".format(page), person=person, tokens=tokens, meetings_count=meetings_count)
