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

import os
import StringIO

from simpletal import simpleTAL

class ViewHandler(object):
  """Base class with general methods for
     view rendering."""

  def path_for(self, view):
    """Builds AppEngine path for a view."""
    return os.path.join(os.path.join(os.path.dirname(__file__), view))

  def macros_from(self, view, context):
    """Fetch macros from a view and injects
       them into a context."""
    source = open(self.path_for(view), 'r')
    macros = simpleTAL.compileXMLTemplate(source)
    source.close()

    context.addGlobal("sitemacros", macros)
    return context

  def render_text(self, view, context):
    """Renderes the TAL view using the context into plain text."""
    source = open(self.path_for(view), 'r')
    template = simpleTAL.compileHTMLTemplate(source)
    source.close()

    text = StringIO.StringIO()
    template.expand(context, text, outputEncoding='utf-8')

    return unicode(text.getvalue(), 'utf-8')
    
  def render_html(self, view, context):
    """Renderes the TAL view using the context into HTML."""
    source = open(self.path_for(view), 'r')
    template = simpleTAL.compileXMLTemplate(source)
    source.close()

    html = StringIO.StringIO()
    docType  = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"' + "\n"
    docType += '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
    template.expand(context, html, outputEncoding='utf-8', docType=docType)

    return unicode(html.getvalue(), 'utf-8')