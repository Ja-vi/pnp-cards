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

#Graphics
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QImage, QPixmap
from PyQt4.QtCore import QSettings, pyqtSlot
from window import Ui_Form as Central

#Image manipulation
from wand.image import Image
from wand.color import Color
from wand.display import display

from history import Command, keep_state

class Border(object):
	"""Represents a border for the cards"""
	black = "black"
	white = "white"
	def __init__(self, colour, wide):
		"""Init the border with a specific *colour* and *wide*"""
		self.colour = colour
		self.wide = wide

def set_changed(func):
	def handler(self, *args, **kwargs):
		self.changed = True
		return func(self, *args, **kwargs)
	return handler

class Card(Command):
	"""Individual object containing an image and actions to manipulate it"""
	def __init__(self, img):
		"""Init a new cards with *img* being a wand.image.Image object"""
		self.img = img
		self.border = None
		self.changed = True
		super(Card, self).__init__()
		self.pixmap()

	@set_changed
	@keep_state("Image setted")
	def set(self, new):
		"""Sets this card to *new* card"""
		self.img.clear()
		self.img.read(blob = new.img.make_blob())
		self.border = new.border

	@set_changed
	def undo(self):
		"""Undo last modifications to this card"""
		super(Card, self).undo()

	@set_changed
	def redo(self):
		"""Redo last undo to this card"""
		super(Card, self).redo()

	@set_changed
	def reset_coords(self):
		self.img.reset_coords()

	@keep_state("Image trimmed")
	def trim(self, fuzz=13):
		"""Trim the border with a threshold *fuzz*"""
		self.img.trim(fuzz = fuzz)
		self.reset_coords()

	@set_changed
	@keep_state("Border setted")
	def set_border(self, border):
		"""Set a new *border* for this card"""
		if self.border is not None:
			self.del_border()
		self.border = border
		self.img.border(Color(self.border.colour), self.border.wide, self.border.wide)

	@keep_state("Image cropped")
	def crop(self, *args, **kwargs):
		"""Crop this card *top*, *bottom*, *left* and *right* pixels"""
		w, h = self.img.size
		if "right" in kwargs:
			kwargs["right"] = w - kwargs["right"]
		if "bottom" in kwargs:
			kwargs["bottom"] = h - kwargs["bottom"]
		self.img.crop(*args, **kwargs)
		self.reset_coords()

	@keep_state("Border deleted")
	def del_border(self):
		"""Remove the border of this card"""
		if self.border is not None:
			w = self.border.wide
			self.crop(top=w, bottom=w, right=w, left=w)
			self.border = None
			self.changed = True

	def save_as(self, filename):
		"""Save this card in a file named *filename*"""
		self.img.save(filename = filename)

	def split(self, rows, cols, separation=0):
		"""Divide this cards in *rows* by *cols* cards, and returns a deck containing them"""
		width, hight = self.img.size
		width, hight = (int(width), int(hight))
		cardWidth = (width - separation * (cols-1)) / cols
		cardHight = (hight - separation * (rows-1)) / rows
		res = []
		for i in range(rows):
			for j in range(cols):
				clon = self.img.clone()
				#TODO is making some weird thing with the destruction of the clon and the creation of the Deck
				clon.crop(top=i*cardHight+i*separation, width=cardWidth, left=j*cardWidth+j*separation, height=cardHight)
				res.append(Card(clon.clone()))
		return Deck(res)

	@set_changed
	@keep_state("Corners rounded")
	def round_corners(self):
		"""Round the corners of the card (setting them to alpha)"""
		pass

	def pixmap(self):
		"""Update and returns the pixmap (QPixmap) of the contained image"""
		if self.changed:
			self._pixmap = QPixmap(QImage.fromData(self.img.make_blob(), self.img.format))
			self.changed = False
		return self._pixmap

class Deck(Command):
	"""Container for the cards and groupal actions"""
	def __init__(self, cards = []):
		self.cards = cards
		super(Deck, self).__init__()

	### Deck methods ###

	@keep_state("PDF loaded")
	def load_from_pdf(self, filename):
		"""Loads all the cards from a pdf with pages compound of images"""
		with Image(filename=filename, resolution=300) as pdf:
			for page in pdf.sequence:
				self.cards.append(Card(Image(page)))

	def split(self, nrows, ncols, sep):
		newcards = Deck()
		for c in self.cards:
			newcards.extend(c.split(nrows, ncols, sep), register=False)
		return newcards

	@keep_state("Loaded images")
	def load(self, filename, cards_row=1, cards_col=1, sep=0):
		"""Load the deck from *filename* having *cards_row* by *cards_col* cards"""
		filename = str(filename)
		if filename.endswith(".pdf"):
			tmpdeck = Deck()
			tmpdeck.load_from_pdf(filename, register=False)
			if cards_row * cards_col > 1:
				tmpdeck = tmpdeck.split(cards_row, cards_col, sep)
			self.extend(tmpdeck)
		else:
			tmpcard = Card(Image(filename = filename))
			if cards_row * cards_col > 1:
				tmpcard = tmpcard.split(cards_row, cards_col, sep)
			else:
				tmpcard = Deck([tmpcard])
			self.extend(tmpcard)

	@keep_state("Cards emptied")
	def clear(self, track=True):
		"""Empty the cards of this deck"""
		while len(self) > 0:
			self.cards.pop()

	@keep_state("Cards resetted")
	def set(self, new):
		"""Set the cards list to *new*"""
		self.clear()
		self.cards.extend(new.cards)

	def get(self, index):
		"""Returns card *index*"""
		return self.cards[index]

	@keep_state("Card deleted")
	def del_card(self, index):
		"""Delete card *index* and return it"""
		return self.cards.pop(index)

	@keep_state("Cards concatenated")
	def extend(self, other):
		self.cards.extend(other.cards)

	def __len__(self):
		"""Number of cards in the deck"""
		return len(self.cards)

	### Multi card methods ###

	@keep_state("Cards trimmed")
	def trim(self, fuzz=15):
		"""Trim all the cards in the deck"""
		for c in self.cards:
			c.trim(fuzz, register=False)

	@keep_state("Borders added")
	def borders(self, colour, wide):
		"""Set a border for all the cards"""
		b = Border(colour, wide)
		for c in self.cards:
			c.set_border(b, register=False)

	@keep_state("Borders removed")
	def del_borders(self):
		"""Remove all the borders of the cards having it"""
		for c in self.cards:
			c.del_border(register=False)

class Page(object):
	"""Image with multiple cards, for printing in diferent card formats and sizes"""
	pass

################## OLD #####################

class MainWindow(QMainWindow, Central):

	def __init__(self):
		QMainWindow.__init__(self)
		Central.__init__(self)
		self.setupUi(self)
		#self.readSettings()
		self.show()
		self.deck = Deck()
		self.init_signals()
		self.say("Cargado")
		self.percent(100)
		self.undo_stack = []

	def init_signals(self):
		self.elegir_boton.clicked.connect(self.handler_open_files)
		#self.guardar_como_boton.clicked.connect(self.saveimgs)
		self.dividir_boton.clicked.connect(self.handler_split)
		self.preview_slider.valueChanged.connect(self.__preview__)
		self.deshacer_boton.clicked.connect(self.undo)
		self.rehacer_boton.clicked.connect(self.redo)
		self.borrar_boton.clicked.connect(self.handler_delete_card)
		self.negro_boton.clicked.connect(self.handler_black_borders)
		self.blanco_boton.clicked.connect(self.handler_white_borders)
		self.quitar_boton.clicked.connect(self.handler_delete_borders)
		self.auto_boton.clicked.connect(self.handler_trim)

	def undo(self):
		pass

	def redo(self):
		pass

	def all_selected(self):
		return self.todas_radio.isChecked()

	def handler_trim(self):
		fuzz = self.umbral_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.trim(fuzz, register=True)
			self.complete_percent()
		else:
			self.deck.get(self.preview_slider.value()).trim(fuzz, register=True)
		self.preview()

	def handler_delete_borders(self):
		if self.all_selected():
			self.reset_percent()
			self.deck.del_borders(register=True)
			self.complete_percent()
		else:
			self.deck.get(self.preview_slider.value()).del_border(register=True)
		self.preview()

	def handler_split(self):
		n = self.n_spin_2.value()
		m = self.m_spin_2.value()
		sep = self.sep_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.set(self.deck.split(n, m, sep))
			self.complete_percent()
		else:
			card = self.deck.del_card(self.preview_slider.value(), register=False)
			self.deck.extend(card.split(n, m, sep), register=True)
		self.say("Completed")
		self.preview(0)

	def handler_open_files(self):
		files = QFileDialog.getOpenFileNames(self, "Elige uno o mas ficheros", "./", "Images (*.png *.jpg);; PDF (*.pdf)")
		if len(files) < 1:
			return
		names = '"' + str(files[0])[str(files[0]).rfind("/")+1:] +'"'
		for el in files[1:]: names += ', "' + str(el)[str(el).rfind("/")+1:] + '"'
		self.fichero_edit.setText(names)
		for file in files:
			self.deck.load(file)
		self.preview(0)
		self.say("Hecho")

	def saveimgs(self):
		name = QFileDialog.getSaveFileName(self, "Nombre del fichero a guardar", "./")
		self.cv.setBaseName(str(name))
		self.cv.writePngFiles()

	def handler_delete_card(self):
		self.deck.del_card(self.preview_slider.value(), register=True)
		self.say("Imagen eliminada")
		if num < len(self.deck):
			self.preview(num)
		else:
			self.preview(-1)

	def handler_black_borders(self):
		wide = self.border_spin.value()
		self.deck.borders(Border.black, wide)
		self.preview()

	def handler_white_borders(self):
		wide = self.border_spin.value()
		self.deck.borders(Border.white, wide)
		self.preview()

	def say(self, text):
		self.msg_label.setText(text)

	def percent(self, num):
		self.progress_bar.setValue(num)

	def reset_percent(self):
		self.percent(0)

	def next_percent(self):
		self.percent(self.progress_bar.value()+100/len(self.deck))

	def complete_percent(self):
		self.percent(100)

	def preview(self, num=None):
		if len(self.deck) > 0:
			self.preview_slider.setMaximum(len(self.deck)-1)
		else:
			self.preview_slider.setMaximum(0)
		if num is not None:
			self.__preview__(num)
		else:
			self.__preview__(self.preview_slider.value())

	def __preview__(self, num):
		self.preview_label.clear()
		try:
			self.preview_label.setPixmap(self.deck.get(num).pixmap())
		except:
			self.preview_label.setText("Image not available")

#	@pyqtSlot()
#	def closeEvent(self, e):
#		settings = QSettings("LuisjaCorp", "PnPCards")
#		settings.setValue("geometry", self.saveGeometry())
#		settings.setValue("windowState", self.saveState())
#		QMainWindow.closeEvent(self, e)

#	def readSettings(self):
#		settings = QSettings("LuisjaCorp", "PnPCards")
#		self.restoreGeometry(settings.value("geometry").toByteArray())
#		self.restoreState(settings.value("windowState").toByteArray())


if __name__ == "__main__":
	app = QApplication(argv)
	window = MainWindow()
	window.show()
	app.exec_()
