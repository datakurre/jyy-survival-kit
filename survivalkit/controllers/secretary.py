#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   This file is part of the Survival-Kit ordering system.
#   Copyright (C) 2009  the Student Union of the University of Jyväskylä,
#                       Asko Soukka <asko.soukka@iki.fi>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import datetime

import wsgiref.handlers

from google.appengine.ext import webapp

from simpletal import simpleTALES

from formencode import htmlfill

from survivalkit.views import ViewHandler
from survivalkit.models import ModelHandler

from survivalkit.models import Collection
from survivalkit.models import Order
from survivalkit.models import ReleaseDate
from survivalkit.models import ExchangeType
from survivalkit.models import Instruction

class MainScreen(ViewHandler):
  def render_form(self, collection=None):
    context = simpleTALES.Context(allowPythonPath=True)

    context.addGlobal("title", "Manage Survival KIT Orders")
    context.addGlobal("root", '/manage/')
    context.addGlobal("orders", Order.uncollected())
    context.addGlobal("download", collection)
    context.addGlobal("collections", Collection.all().order('created'))
    context.addGlobal("release_dates", ReleaseDate.all().order('date'))
    context.addGlobal("exchange_types", ExchangeType.all().order('type'))   
    context.addGlobal("instructions", Instruction.all().order('topic'))

    return self.render_html("secretary.pt", self.macros_from("master.pt", context))

class Default(webapp.RequestHandler, MainScreen):
  def get(self):
    self.response.out.write(self.render_form())

class Create(webapp.RequestHandler, ModelHandler, MainScreen):
  def post(self, model):
    if model in ['Collection']:
      collection = self.create('Collection', {'created': datetime.datetime.now()}).put()
      for order in self.request.get_all('order'):
        order = Order.get(order)
        order.collection = collection
        order.put()
      self.response.out.write(self.render_form(collection))
    elif model in ['ReleaseDate', 'ExchangeType', 'Instruction']:
      values = self.extract(model, self.request)
      errors = self.validate(model, values)
      if not errors:
        self.create(model, values).put()
        self.redirect("/manage/")
      else:
        self.response.out.write(htmlfill.render(self.render_form(), values, errors,
                                                force_defaults=False, encoding='utf-8'))
    else:
      self.error(404)

class Download(webapp.RequestHandler, ModelHandler):
  def get(self, model, key):
    if model in ['Collection']:
      collection = Collection.get(key)
      self.response.headers['Content-Type'] = "application/vnd.oasis.opendocument.spreadsheet"
      self.response.headers['Content-Disposition'] = "filename=Survival-Kit-Orders_%s.ods" % collection.created.strftime("%Y-%m-%d")
      self.response.out.write(collection.sheet())
    else:
      self.error(404)

class Delete(webapp.RequestHandler, ModelHandler):
  def get(self, model, key=None):
    if model in ['Collection']:
      collection = Collection.get(key)
      for order in collection.order_set:
        for kit in order.kit_set:
          kit.delete()
        order.delete()
      collection.delete()
      self.redirect("/manage/")
    elif model in ['ReleaseDate', 'ExchangeType', 'Instruction']:
      self.destroy(key or self.request.get_all('key'))
      self.redirect("/manage/")
    else:
      self.error(404)

class Update(webapp.RequestHandler, ModelHandler, MainScreen):
  def post(self, model, key=None):
    if model in ['Instruction']:
      values = self.extract(model, self.request, prefix="%(key)s_" % vars())
      errors = self.validate(model, values)
      if not errors:
        self.update(model, key, values).put()
        self.redirect("/manage/")
      else:
        real_errors = {}
        real_values = {}
        for field in errors.keys():
          real_errors["%(key)s_%(field)s" % vars()] = errors[field]
        for field in values.keys():
          real_values["%(key)s_%(field)s" % vars()] = values[field]



        self.response.out.write(htmlfill.render(self.render_form(), real_values, real_errors,
                                                force_defaults=False, encoding='utf-8'))
    else:
      self.error(404)

def main():
  application = webapp.WSGIApplication([
      ('/manage/', Default),
      ('/manage/([^/]*)/create', Create),
      ('/manage/([^/]*)/delete', Delete),
      ('/manage/([^/]*)/([^/]*)/update', Update),
      ('/manage/([^/]*)/([^/]*)/delete', Delete),
      ('/manage/([^/]*)/([^/]*)/download', Download),
    ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__': main()