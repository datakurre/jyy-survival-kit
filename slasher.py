#!/usr/bin/python# -*- coding: utf-8 -*-##   This file is part of the Survival-Kit ordering system.#   Copyright (C) 2009  the Student Union of the University of Jyväskylä,#                       Asko Soukka <asko.soukka@iki.fi>##   This program is free software: you can redistribute it and/or modify#   it under the terms of the GNU General Public License as published by#   the Free Software Foundation, either version 3 of the License, or#   (at your option) any later version.##   This program is distributed in the hope that it will be useful,#   but WITHOUT ANY WARRANTY; without even the implied warranty of#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#   GNU General Public License for more details.##   You should have received a copy of the GNU General Public License#   along with this program.  If not, see <http://www.gnu.org/licenses/>.#

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