#!/usr/bin/python

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
        self.response.out.write(htmlfill.render(self.render_form(), values, errors, encoding='utf-8'))
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
    
def main():
  application = webapp.WSGIApplication([
      ('/manage/', Default),
      ('/manage/([^/]*)/create', Create),
      ('/manage/([^/]*)/delete', Delete),
      ('/manage/([^/]*)/([^/]*)/delete', Delete),
      ('/manage/([^/]*)/([^/]*)/download', Download),
    ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__': main()