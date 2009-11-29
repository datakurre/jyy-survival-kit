#!/usr/bin/python

import wsgiref.handlers

from google.appengine.ext import webapp

class AddTrailingSlash(webapp.RequestHandler):
  def get(self, path, target):
    self.redirect("%(path)s/%(target)s/" % vars())

def main():
  application = webapp.WSGIApplication([
      ('^(.*)/([^/]*)$', AddTrailingSlash),
    ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__': main()