import json
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        cookie = self.get_secure_cookie("ZoomToWebex-User", max_age_days=1, min_version=2)
        #print("Cookie:{0}".format(cookie))
        return cookie
