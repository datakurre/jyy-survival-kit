Download source: http://ooolib.sourceforge.net/
Licensed under: LGPL 2.1
Required files: ooolib/__init__.py
Tested with version: ooolib-python-0.0.16

The included source has been modified from the original
ooolib-python-0.0.16 with the following changes:

--- ooolib.py	2008-07-31 08:13:54.000000000 +0300
+++/ooolib/__init__.py 2009-03-08 11:46:37.000000000 +0200
@@ -1119,6 +1119,7 @@
 		self._zip_insert(self.savefile, "settings.xml", self._ods_settings())
 		if self.debug: print "  styles.xml"
 		self._zip_insert(self.savefile, "styles.xml", self._ods_styles())
+		self.savefile.close()
 
 	def _zip_insert(self, file, filename, data):
 		"Insert a file into the zip archive"
@@ -1752,6 +1753,7 @@
 		# self._zip_insert(self.savefile, "settings.xml", self._odt_settings())
 		if self.debug: print "  styles.xml"
 		# self._zip_insert(self.savefile, "styles.xml", self._odt_styles())
+		self.savefile.close()
 
 	def _zip_insert(self, file, filename, data):
 		now = time.localtime(time.time())[:6]