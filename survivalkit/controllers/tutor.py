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

import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import mail

from simpletal import simpleTALES

from formencode import htmlfill

from survivalkit import __SECRETARY__

from survivalkit.views import ViewHandler
from survivalkit.models import ModelHandler

from survivalkit.models import Order
from survivalkit.models import Kit
from survivalkit.models import ReleaseDate
from survivalkit.models import ExchangeType
from survivalkit.models import Instruction

class MainScreen(ViewHandler):
  def render_form(self, rows=1):
    context = simpleTALES.Context(allowPythonPath=True)

    context.addGlobal("title", "JYY Survival Kit Order Form")
    context.addGlobal("root", '/')
    context.addGlobal("rows", rows)
    context.addGlobal("release_dates", ReleaseDate.all().order('date'))
    context.addGlobal("exchange_types", ExchangeType.all().order('type'))
    context.addGlobal("instructions", Instruction.all().order('topic'))

    return self.render_html("tutor.pt", self.macros_from("master.pt", context))

class Default(webapp.RequestHandler, ModelHandler, MainScreen):
  def get(self):
    """Renders an empty form."""
    # Running through htmlfill.render() removes non-standard form:error-tags from the template.
    self.response.out.write(htmlfill.render(self.render_form(), None, None,
                                            force_defaults=False, encoding='utf-8'))

  def post(self):
    """Handles all form submissions."""
    ## Decides the current action
    action = self.request.get('add') and "add" \
               or self.request.get('remove') and "remove" \
               or self.request.get('order') and "order"
  
    ## Retrieves submitted data
    tutor = self.extract('Order', self.request, skip=['collection'])
  
    kits = []
    for i in range(1, int(self.request.get('rows') or 0) + 1):
      if action is not "remove" or not self.request.get("%(i)s_removable" % vars()):
        kit = self.extract('Kit', self.request, prefix="%(i)s_" % vars(), skip=['order'])
        ## Append kit only if it has any values filled:
        if [value for value in kit.items() if value[1] is not None]: 
          kits.append(kit)

    errors = self.validate('Order', tutor, skip=['collection'])
    for i in range(1, len(kits) + 1):
        kit_errors = self.validate('Kit', kits[i-1], skip=['order'])
        for key in kit_errors:
          errors["%(i)s_%(key)s" % vars()] = kit_errors[key]

    ## Returns an incomplete form
    if len(kits) == 0 or errors or action in ['add', 'remove']:
      defaults = tutor.copy()
      for i in range(1, len(kits) + 1):
        for key in kits[i-1]:
          defaults["%(i)s_%(key)s" % vars()] = kits[i-1][key]
      
      ## Ensures that there is always at least one kit 
      defaults['rows'] = len(kits)
      if defaults['rows'] == 0 or action in ['add']:
        defaults['rows'] += 1

      self.response.out.write(htmlfill.render(self.render_form(defaults['rows']), defaults, errors,
                                              force_defaults=False, encoding='utf-8'))
    ## Places the orders and returns confirmation for the order
    else:
      ## Saves the orders
      order = self.create('Order', tutor).put()
      for kit in kits:
        kit['order'] = order
        self.create('Kit', kit).put()

      ## Posts and renders the confirmation
      context = simpleTALES.Context(allowPythonPath=True)

      context.addGlobal("title", "JYY Survival Kit Order Confirmation")
      context.addGlobal("root", '/')
      context.addGlobal("tutor", tutor)
      context.addGlobal("order", kits)

      message = mail.EmailMessage(sender=__SECRETARY__, subject="Confirmation for your Survival Kit order")
      message.to = "%s %s <%s>" % (tutor['first_name'], tutor['last_name'], tutor['email'])
      message.body = self.render_text("tutor-mail.pt", context)
      
      try:
        message.send()
      except:
        pass
        
      message = mail.EmailMessage(sender=__SECRETARY__, subject="[KIT Order] %s kit%s for %s %s" % \
                 (len(kits), len(kits) > 1 and "s" or "", tutor['first_name'], tutor['last_name']))
      message.reply_to = "%s %s <%s>" % (tutor['first_name'], tutor['last_name'], tutor['email'])
      message.to = __SECRETARY__
      message.body = self.render_text("secretary-mail.pt", context)

      try:
        message.send()
      except:
        pass

      html = self.render_html("tutor-confirmation.pt", self.macros_from("master.pt", context))      
      self.response.out.write(html)

def main():
  application = webapp.WSGIApplication([
      ('/', Default),
    ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__': main()