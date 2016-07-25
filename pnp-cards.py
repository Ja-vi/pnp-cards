#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
Copyright 2015, Luis Javier Gonzalez (luis.j.glez.devel@gmail.com)

This program is licensed under the GNU GPL 3.0 license.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from sys import argv
import json
import math
from copy import deep_copy

#Graphics
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QImage, QPixmap
from PyQt4.QtCore import QSettings, pyqtSlot
from window import Ui_Form as Central

#Image manipulation
from wand.image import Image
from wand.color import Color
from wand.display import display


"""
-history empieza con [[]] es decir, un array de pngs vacio. tamaño = 1, maxhist = 0, currenthist = 0
-cuando se realiza cualquier accion: abrir ficheros, dividir, quitar bordes, poner bordes, agrupar, ... se hace la accion y se añade el nuevo array al historial. [[], [imagen1,imagen2,imagen3]] tamaño = 2, maxhist = 1, currenthist = 1
-cuando se deshace [[], [imagen1,imagen2,imagen3]] tamaño = 2, maxhist = 1, currenthist = 0 -> debemos mostrar y trabajar con el array []
-cuando se rehace [[], [...]] tamaño = 2, maxhist = 1, currenthist = 1 -> mostrar y trabajar con [...]
-cuando hacemos algo habiendo dado a deshacer anteriormente [[],[...]] primero sacamos todos los elementos necesarios hasta que maxhist == currenthist y despues añadimos el elementoal historial.

Formato del fichero de modos en json:
[ [NombreDeLaConfiguracion, QuieresBorde?, color (0,1) , EsquinasRedondeadas?, Formato (0,1,2), N,M], [...], ... ]
"""

class State(object):
	"""Each of the states saved in a history"""
	def __init__(self, obj, msg=None):
		"""*obj* is the object to freeze in this state, *msg* the status message"""
		self.obj = deep_copy(obj)
		self.msg = msg

	def get_obj(self):
		"""Returns a copy of the object and the message preserving the state intact"""
		return deep_copy(obj)

	def get_msg(self):
		return msg

class History(object):
	"""Keeps a number of states for a given object"""
	def __init__(self, obj):
		"""*card* to keep track here"""
		self.obj = obj
		self.states = [State(obj, "Card created")]
		self.current_state = 1
		self.length = 50

	def track(self, msg="Default message")
		"""Add a new state to the states list, just after the current state"""
		while self.current_state < len(self.states):
			self.states.pop()
		if len(self.states) == self.length:
			self.states.pop(0)
			self.current.state -= 1
		self.states.append(State(self.obj), msg)
		self.current_state += 1

	def undo(self):
		"""Undo one action"""
		if self.current_state > 1:
			self.current_state -= 1

	def redo(self):
		"""Redo one action"""
		if self.current_state < len(self.states):
			self.current_state += 1

	def msg_current(self):
		return self.states[self.current_state - 1].get_msg()

	def get_current(self)
		return self.states[self.current_state - 1].get_obj()

class Border(object):
	"""Represents a border for the cards, it can be in diferent colours"""
	#predefined colours
	black = "black"
	white = "white"

	def __init__(self, colour, wide):
		"""Init the border with a specific *colour* and *wide*"""
		self.colour = colour
		self.wide = wide

class Card(object):
	"""Individual object containing an image and actions to manipulate it"""
	def __self__(self, img):
		"""Init a new cards with *img* being a wand.image.Image object"""
		self.img = img
		self.history = History(self.img)
		self.border = None

	def undo(self):
		"""Undo last modifications to this card"""
		self.history.undo()
		self.img = self.history.get_current()

	def reset_coord(self):
		self.img.reset_coords()

	def trim(self, fuzz):
		"""Trim the border with a threshold *fuzz*"""
		self.img.trim(fuzz = fuzz)
		self.reset_coords()

	def round_corners(self):
		"""Round the corners of the card (setting them to alpha)"""
		pass

	def set_border(self, border):
		"""Set a new *border* for this card"""
		if self.border is not None:
			self.del_border()
		self.border = border
		self.img.border(self.border.colour, self.border.wide, self.border.wide)

	def crop(self, *args, **kwargs):
		"""Crop this card *top*, *bottom*, *left* and *right* pixels"""
		w, h = self.img.size
		if "right" in kwargs:
			kwargs["right"] = w - kwargs["right"]
		if "bottom" in kwargs:
			kwargs["bottom"] = h - kwargs["bottom"]
		self.img.crop(args, kwargs)
		self.reset_coords()

	def del_border(self):
		"""Remove the border of this card"""
		if border is not None:
			w = self.border.wide
			cw, ch = self.img.size
			self.crop(top=w, bottom=ch-w, right=cw-w, left=w)
			self.border = None

	def save_as(self, filename):
		"""Save this card in a file named *filename*"""
		self.img.save(filename = filename)

	def split(self, rows, cols):
		"""Divide this cards in *rows* by *cols* cards"""
		pass

class Deck(object):
	"""Container for the cards and groupal actions"""
	def __init__(self):
		self.cards = []
		self.history = History(self.cards)
		#self.undo_stack = []

	def load_from_pdf(self, filename):
		"""Loads all the cards from a pdf with pages compound of images"""
		with Image(filename=filename, resolution=300) as pdf:
			for page in pdf.sequence:
				self.cards.append(Card(Image(page)))

	def split(self, nrows, ncols):
		newcards = []
		for c in self.cards:
			newcards.extend(c.split(nrows, ncols))
		return newcards

	def load(self, filename, cards_row=1, cards_col=1):
		"""Load the deck from *filename* having *cards_row* by *cards_col* cards"""
		if filename.endswith(".pdf"):
			tmpdeck = Deck()
			tmpdeck.load_from_pdf(filename)
			self.cards.extend(tmpdeck.split(cards_row, cards_col))
		else:
			tmpcard = Card(Image(filename = filename))
			self.cards.extend(tmpcard.split(cards_row, cards_col))
		self.history.track("Loaded Images")

	def empty(self):
		"""Empty the cards of this deck"""
		while len(self.cards) > 0:
			self.cards.pop()
		self.history.track("Emptied cards")

	def undo(self):
		"""Undo last modification of this deck"""
		self.history.undo()
		self.cards = self.history.get_current()

	def trim(fuzz = fuzz):
		"""Trim all the cards in the deck"""
		for c in self.cards:
			c.trim(fuzz)

	def __len__(self):
		"""Number of cards in the deck"""
		return len(self.cards)

	def get_card(self, index):
		return self.cards[i]

	def white_borders(self):
		b = Border(Border.white, 10)
		for c in self.cards:
			c.set_border(b)

	def black_borders(self):
		b = Border(Border.black, 10)
		for c in self.cards:
			c.set_border(b)

class Page(object):
	"""Image with multiple cards, for printing in diferent card formats and sizes"""
	pass

################## OLD #####################

class MainWindow(QMainWindow, Central):

	def __init__(self):
		QMainWindow.__init__(self)
		Central.__init__(self)
		self.setupUi(self)
		self.readSettings()
		self.show()

		self.deck = Deck()
		self.setSignals()
		self.say("Cargado")
		self.percent(100)

	def setSignals(self):
		self.elegir_boton.clicked.connect(self.openfil)
		self.guardar_como_boton.clicked.connect(self.saveimgs)
		self.dividir_boton.clicked.connect(self.divide)
		self.preview_slider.valueChanged.connect(self.preview)
		self.deshacer_boton.clicked.connect(self.cv.undo)
		self.rehacer_boton.clicked.connect(self.cv.redo)
		self.borrar_boton.clicked.connect(self.borrarimg)
		self.negro_boton.clicked.connect(self.ponerBordeNegro)
		self.blanco_boton.clicked.connect(self.ponerBordeBlanco)
		self.quitar_boton.clicked.connect(self.recortarBorde)
		self.auto_boton.clicked.connect(self.handler_trim)

	def handler_trim(self):
		fuzz = self.umbral_spin.value()
		if self.todas_radio.isChecked():
			self.deck.trim(fuzz)
		else:
			self.deck.get_card(self.preview_slider.value()).trim(fuzz)
		self.updatePreview()
		self.cv.saveHistory()

	def recortarBorde(self):
		if self.todas_radio.isChecked():
			self.resetPercent()
			for el in self.cv.png:
				w, h = el.size
				ri = w - self.right_spin.value()
				bo = h - self.bottom_spin.value()
				el.crop(left = self.left_spin.value(), top = self.top_spin.value(), right = ri, bottom = bo)
				el.reset_coords()
				self.nextPercent()
			self.completePercent()
		else:
			el = self.cv.png[self.preview_slider.value()]
			w, h = el.size
			ri = w - self.right_spin.value()
			bo = h - self.bottom_spin.value()
			el.crop(left = self.left_spin.value(), top = self.top_spin.value(), right = ri, bottom = bo)
			el.reset_coords()
		self.updatePreview()
		self.cv.saveHistory()

	def split(self, im, n, m):
		width, hight = im.size
		sep = self.sep_spin.value()
		width, hight = (int(width), int(hight))
		cardWidth = (width - sep * (m-1)) / m
		cardHight = (hight - sep * (n-1)) / n
		res = []
		for i in range(n):
			for j in range(m):
				with im.clone() as clon:
					clon.crop(top=i*cardHight+i*sep, width=cardWidth, left=j*cardWidth+j*sep, height=cardHight)
					res.append(clon.clone())
		return res

	def divide(self):
		n = self.n_spin_2.value()
		m = self.m_spin_2.value()
		images = self.cv.getPngList()
		end_images = []
		self.resetPercent()
		for el in images:
			end_images.extend(self.split(el, n, m))
			self.nextPercent(images)
		self.completePercent()
		self.say("Divididas")
		self.cv.setPngList(end_images)
		self.updatePreview(0)
		self.cv.saveHistory()

	def openfil(self):
		files = QFileDialog.getOpenFileNames(self, "Elige uno o mas ficheros", "./", "Images (*.png *.jpg);; PDF (*.pdf)")
		if len(files) < 1:
			return
		names = '"' + str(files[0])[str(files[0]).rfind("/")+1:] +'"'
		for el in files[1:]: names += ', "' + str(el)[str(el).rfind("/")+1:] + '"'
		self.fichero_edit.setText(names)
		self.cv.imgImport(files)
		self.updatePreview(0)
		self.cv.saveHistory()
		self.say("Hecho")

	def saveimgs(self):
		name = QFileDialog.getSaveFileName(self, "Nombre del fichero a guardar", "./")
		self.cv.setBaseName(str(name))
		self.cv.writePngFiles()

	def borrarimg(self):
		num = self.preview_slider.value()
		self.say("Borrando")
		self.cv.png.pop(num)
		self.say("Imagen eliminada")
		if num < len(self.cv.png):
			self.updatePreview(num)
		else:
			self.updatePreview(-1)
		self.cv.saveHistory()

#	def ponerBordeNegro(self):
#		tam = self.border_spin.value()
#		for im in self.cv.png:
#			im.border(Color("black"), tam, tam)
#		self.updatePreview()
#		self.cv.saveHistory()

#	def ponerBordeBlanco(self):
#		tam = self.border_spin.value()
#		for im in self.cv.png:
#			im.border(Color("white"), tam, tam)
#		self.updatePreview()
#		self.cv.saveHistory()

	def say(self, text):
		self.msg_label.setText(text)

	def percent(self, num):
		self.progress_bar.setValue(num)

	def resetPercent(self):
		self.percent(0)

	def nextPercent(self, lis=None):
		if lis == None:
			self.percent(self.progress_bar.value()+100/len(self.cv.png))
		else:
			self.percent(self.progress_bar.value()+100/len(lis))

	def completePercent(self):
		self.percent(100)

	def updatePreview(self, num = None):
		if len(self.cv.png)>0:
			self.preview_slider.setMaximum(len(self.cv.png)-1)
		else:
			self.preview_slider.setMaximum(0)
		if num == None:
			self.preview(self.preview_slider.value())
		else:
			self.preview(num)

	def preview(self, num):
		self.preview_label.clear()
		try:
			self.preview_label.setPixmap(QPixmap(QImage.fromData(self.cv.png[num].make_blob(), self.cv.png[num].format)))
		except:
			self.preview_label.setText("Sin imagenes")

	@pyqtSlot()
	def closeEvent(self, e):
		settings = QSettings("LuisjaCorp", "PnPCards")
		settings.setValue("geometry", self.saveGeometry())
		settings.setValue("windowState", self.saveState())
		QMainWindow.closeEvent(self, e)

	def readSettings(self):
		settings = QSettings("LuisjaCorp", "PnPCards")
		self.restoreGeometry(settings.value("geometry").toByteArray())
		self.restoreState(settings.value("windowState").toByteArray())


if __name__ == "__main__":
	app = QApplication(argv)
	window = MainWindow()
	window.show()
	app.exec_()
