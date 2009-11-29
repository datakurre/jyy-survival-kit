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

import StringIO

from google.appengine.ext import db

from formencode import validators
from formencode.api import Invalid

import ooolib

class ModelHandler(object):
  """Base class with general methods for
     model creation and deletion."""

  def extract(self, model, request, prefix="", skip=[]):
    """Extracts a dictionary of values for the model from the request."""
    # XXX Property classes db.ListProperty and db.StringListProperty are not supported
    dictionary = {}
    properties = eval(model).properties()
    # Sometimes the browser have been forced to use e.g. "iso-8859-1" charset, even
    # when the page is told to be in "utf-8". That might raise UnicodeDecodeError,
    # or just lose part of the input (when unicode_errors="ignore"). That's because
    # we read the first "accepted_charset" from headers (fallback to "iso-8859-1")
    # try to decode the input with that whenever a unicode error is met.
    default_charset = request.charset
    alternative_charset = request.accept_charset.best_matches()
    alternative_charset = alternative_charset and alternative_charset[0] or 'iso-8859-1'
    for key in [key for key in properties if key not in skip]:
      default_value = request.get(prefix + key, default_value="")
      try:
        request.unicode_errors = "strict"
        value = request.get(prefix + key, default_value="")
      except UnicodeDecodeError:
        try:
          request.charset = alternative_charset
          value = request.get(prefix + key, default_value="")
        except:
          value = default_value
      request.unicode_errors = "ignore"
      request.charset = default_charset
      dictionary[key] = self.accommodate(value, properties[key].__class__)
    return dictionary

  def accommodate(self, string, property_class):
    """Accommodates the string to match with the base type of the property class."""
    return {
      # XXX Only the property classes listed below are supported
      db.StringProperty: lambda x: x.strip() or None,
      db.IntegerProperty: lambda x: int(x.strip()),
      }[property_class](string)

  def translate(self, error):
    """Translates a validation error into
       a more human readable form."""
    if error.endswith("is required"):
      return "This field is mandatory"
    return error

  def validate(self, model, dictionary, skip=[]):
    """Validates values in the dictionary by the model
       and returns a dictionary of errors."""
    errors = {}
    properties = eval(model).properties()
    for key in [key for key in properties if key not in skip]:
      try:
        properties[key].validate(dictionary[key])
      except db.BadValueError, e:
        errors[key] = self.translate(e.message)
    ## Extra validation for e-mail addresses
    if dictionary.has_key('email'):
      validator = validators.Email()
      try:
        validator.to_python(dictionary['email'])
      except Invalid, e:
        errors['email'] = e.message
    return errors

  def create(self, model, dictionary):
    """Creates an entity of the model from
       the values in the dictionary."""
    return eval(model)(**dictionary)

  def destroy(self, keys):
    """Deletes entities by keys."""
    db.delete(keys)

## This is how the secretary sees the information,
## but I decided to make the model a bit simpler
#
# class Tutor(db.Model):
#   """Tutor is a person that can make kit orders
#      for her tutorees (students)."""
#   first_name = db.StringProperty(required=True)
#   last_name = db.StringProperty(required=True)
#   email = db.StringProperty(required=True)
#   phone = db.StringProperty(required=False)
#
# class Order(db.Model):
#   """Every order is made by a tutor."""
#   tutor = db.ReferenceProperty(Tutor)
#
# class Student(db.Model):
#   """Student is a person to whom her tutor has
#      ordered a kit in some the orders."""
#   order = db.ReferenceProperty(Order)
#   first_name = db.StringProperty(required=True)
#   last_name = db.StringProperty(required=True)
#   kit_release_date = db.StringProperty(required=False)
#   duration_of_exchange = db.StringProperty(required=True)

## Although, the following is how the system sees the model
## and is probably the simplest way to implement it.

class Collection(db.Model):
  """Collection consists from the orders, which the
     secretary have selected to handle at time."""
  created = db.DateTimeProperty(required=True)

  def sheet(self):
    sheet = ooolib.Calc(); row = 1
    for order in self.order_set:
      for kit in order.kit_set:
        sheet.set_cell_value(1, row, "string", "%s %s" % (order.last_name, order.first_name))
        if order.phone:
          sheet.set_cell_value(2, row, "string", "%s, %s" % (order.email, order.phone))
        else:
          sheet.set_cell_value(2, row, "string", order.email)
        sheet.set_cell_value(3, row, "string", "%s %s" % (kit.last_name, kit.first_name))
        sheet.set_cell_value(4, row, "string", kit.release_date or "")
        sheet.set_cell_value(8, row, "string", kit.exchange_type)
        row += 1
    file = StringIO.StringIO()
    sheet.save(file)
    return file.getvalue()
    
  @property
  def kit_count(self):
    total = 0
    for order in self.order_set:
      total += order.kit_set.count()
    return total

class Order(db.Model):
  """Order is made by a tutor and therefore tutor's
     contact information must be enclosed."""
  collection = db.ReferenceProperty(Collection, required=False)
  first_name = db.StringProperty(required=True)
  last_name  = db.StringProperty(required=True)
  email      = db.StringProperty(required=True)
  phone      = db.StringProperty(required=False)

  @classmethod
  def uncollected(cls):
    return cls.gql("WHERE collection = :1 ORDER BY last_name", None)

class Kit(db.Model):
  """Kit is actually a part of an order. Kit encloses
     information about the student to whom the kit
     was ordered to, the date it should be releaseable,
     and type of student's exchange. The type (usually
     the duration of the exchange) affects to
     the price of the kit."""
  order        = db.ReferenceProperty(Order, required=True)
  first_name   = db.StringProperty(required=True)
  last_name    = db.StringProperty(required=True)
  # Because the available release dates and exchange types
  # may change by time, they must not be references, but copied
  # descriptions of the options selected, when ordering kits.
  release_date  = db.StringProperty(required=False)
  exchange_type = db.StringProperty(required=True)

class ReleaseDate(db.Model):
  """A possible release date to be selected,
     when ordering a kit."""
  date = db.StringProperty(required=True)

class ExchangeType(db.Model):
  """A possible duration of exchange to be selected,
     when ordering a kit."""
  type = db.StringProperty(required=True)

class Instruction(db.Model):
  """An instruction to show on below of the order form."""
  topic = db.StringProperty(required=True)
  details = db.StringProperty(required=True)