import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from django.utils import simplejson

def _trace():
    import pdb, sys
    debugger = pdb.Pdb(stdin=sys.__stdin__, 
        stdout=sys.__stdout__)
    debugger.set_trace(sys._getframe().f_back)

class URLTag(db.Model):
    user = db.UserProperty()
    url = db.LinkProperty()
    freebase_id = db.StringProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)

class RequestHandler(webapp.RequestHandler):
    def return_json(self, json):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(simplejson.dumps(json))

class TagCreate(RequestHandler):
    # just for debugging!
    def get(self):
        return self.post()

    def post(self):
        # maybe we should disallow multiple tags by the same user?
        # or maybe one replaces the other?

        user = users.get_current_user()
        url = self.request.get("url") # we should normalize the url!
        freebase_id = self.request.get("id")
        tag = URLTag(user=user, url=url, freebase_id=freebase_id)
        db.put(tag)
        self.return_json({"status":'success'})

def urltags_to_json(urltags):
    return [{"id":result.freebase_id,
                           "url": result.url,
                           "user_email": result.user.email() if result.user else None,
                           "user_id": result.user.user_id() if result.user else None} for result in urltags]

class URLTags(RequestHandler):
    """
    Gets all the tags for a given URL
    
    (probably good just for debug mode...there could be too 
    many to shove down the wire at some point)
    """
    def get(self):
        url = self.request.get("url")
        query = db.GqlQuery("SELECT * FROM URLTag where url = :1", url)
        results = query.fetch(10000)
        self.return_json(urltags_to_json(results))


class UserTags(RequestHandler):
    def get(self):
        user_email = self.request.get("user")
        user = users.User(email=user_email)
        query = db.GqlQuery("SELECT * FROM URLTag where user = :1", user)
        results = query.fetch(10000)
        self.return_json(urltags_to_json(results))

        
class  MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/"))

        self.response.out.write("<html><body>%s</body></html>" % greeting)


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/tag/create', TagCreate),
                                      ('/url/tags', URLTags),
                                      ('/user/tags', UserTags)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
