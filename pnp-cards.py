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
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QImage, QPixmap, QPrinter, QGraphicsScene, QGraphicsView, QPainter
from PyQt4.QtCore import QSettings, pyqtSlot, Qt
from window import Ui_Form as Central

#Image manipulation
from wand.image import Image
from wand.color import Color

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

class Card(object):
	"""Individual object containing an image and actions to manipulate it.
	Posible kwargs to __init__ are filename, file, image, blob. it will load the image from there"""
	def __init__(self, *args, **kwargs):
		"""Init a new cards with *img* being a wand.image.Image object"""
		self.img = Image(*args, **kwargs)
		self.border = None
		self.changed = True
		self.pixmap()

	def __del__(self):
		self.img.destroy()

	@set_changed
	def reset_coords(self):
		self.img.reset_coords()

	@set_changed
	def set_border(self, border):
		"""Set a new *border* for this card"""
		if self.border is not None:
			self.del_border()
		self.border = border
		with Color(self.border.colour) as colour:
			self.img.border(colour, self.border.wide, self.border.wide)

	def crop(self, *args, **kwargs):
		"""Crop this card *top*, *bottom*, *left* and *right* pixels"""
		w, h = self.img.size
		if "right" in kwargs:
			kwargs["right"] = w - kwargs["right"]
		if "bottom" in kwargs:
			kwargs["bottom"] = h - kwargs["bottom"]
		self.img.crop(*args, **kwargs)
		self.reset_coords()

	def del_border(self):
		"""Remove the border of this card"""
		if self.border is not None:
			w = self.border.wide
			self.crop(top=w, bottom=w, right=w, left=w)
			self.border = None
			self.changed = True

	def trim(self, fuzz=13):
		self.img.trim(fuzz=fuzz)
		self.reset_coords()

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
				with self.img.clone() as clon:
					clon.crop(top=i*cardHight+i*separation, width=cardWidth, left=j*cardWidth+j*separation, height=cardHight)
					clon.reset_coords()
					res.append(Card(image=clon))
		return Deck(res)

	@set_changed
	def round_corners(self):
		"""Round the corners of the card (setting them to alpha)"""
		pass

	def pixmap(self):
		"""Update and returns the pixmap (QPixmap) of the contained image"""
		if self.changed:
			self._pixmap = QPixmap(QImage.fromData(self.img.make_blob(), self.img.format))
			self.changed = False
		return self._pixmap

class Deck(object):
	"""Container for the cards and groupal actions"""
	def __init__(self, cards):
		self.cards = cards

	### Iterator methods ###

	def __getitem__(self, index):
		"""Indexed access to cards"""
		return self.cards[index]

	def __len__(self):
		"""Number of cards in the deck"""
		return len(self.cards)

	### Deck methods ###

	def load_from_pdf(self, filename):
		"""Loads all the cards from a pdf with pages compound of images"""
		with Image(filename=filename, resolution=200) as pdf:
			for page in pdf.sequence:
				with Image(page).convert('png') as new:
					self.append(Card(image=new))

	def load(self, filename, cards_row=1, cards_col=1, sep=0):
		"""Load the deck from *filename* having *cards_row* by *cards_col* cards"""
		filename = str(filename)
		tmp = Deck([])
		if filename.endswith(".pdf"):
			tmp.load_from_pdf(filename)
		else:
			tmp.append(Card(filename=filename))

		if cards_row * cards_col > 1:
			tmp = tmp.split(cards_row, cards_col, sep)
		self.extend(tmp)

	def clear(self, track=True):
		"""Empty the cards of this deck"""
		while len(self) > 0:
			self.cards.pop()

	def del_card(self, index):
		"""Delete card *index* and return it"""
		return self.cards.pop(index)

	def extend(self, other):
		"""Extend from another dictionary or list of cards"""
		if isinstance(other, list):
			self.cards.extend(other)
		elif isinstance(other, Deck):
			self.cards.extend(other.cards)

	def append(self, card):
		"""Add a new card to the deck"""
		self.cards.append(card)

	### Multi card methods ###

	def join(self, fils, cols, sep=0, **kwargs):
		"""Set the cards to be the junction of the previous cards"""

		rest = len(self) % (fils * cols)
		while (rest):
			self.append(self[0])
			rest -= 1

		numcards = len(self) / (fils * cols)
		format = self[0].img.format
		w = self[0].img.width
		h = self[0].img.height
		newdeck = Deck([])

		for c in range(numcards):
			with Image(width = w * cols + sep * (cols-1), height = h * fils + sep * (fils-1)) as joint:
				for i in range(fils):
					for j in range(cols):
						joint.composite(self[c*fils*cols + i*cols + j].img, top=(h+sep)*i, left=(w+sep)*j)
						if "call" in kwargs:
							if callable(kwargs["call"]):
								kwargs["call"]()
				newdeck.append(Card(blob=joint.make_blob(format)))

		self.clear()
		self.extend(newdeck)

	def split(self, nrows, ncols, sep, **kwargs):
		newcards = Deck([])
		for c in self.cards:
			newcards.extend(c.split(nrows, ncols, sep))
			if "call" in kwargs:
				if callable(kwargs["call"]):
					kwargs["call"]()
		self.clear()
		self.extend(newcards)

	def borders(self, colour, wide, **kwargs):
		"""Set a border for all the cards"""
		b = Border(colour, wide)
		for c in self.cards:
			c.set_border(b)
			if "call" in kwargs:
				if callable(kwargs["call"]):
					kwargs["call"]()

	def del_borders(self, **kwargs):
		"""Remove all the borders of the cards having it"""
		for c in self.cards:
			c.del_border()
			if "call" in kwargs:
				if callable(kwargs["call"]):
					kwargs["call"]()

	def trim(self, fuzz=13, **kwargs):
		"""Trim all the cards with a *fuzz* factor of similitude between colours"""
		for c in self.cards:
			c.trim(fuzz)
			if "call" in kwargs:
				if callable(kwargs["call"]):
					kwargs["call"]()

	def crop(self, **kwargs):
		"""Crop all the cards by kwargs px"""
		notif = None
		if "call" in kwargs:
			notif = kwargs["call"]
			del kwargs["call"]
		for c in self.cards:
			c.crop(**kwargs)
			if callable(notif):
				notif()

class Printer(object):
	"""For printing in diferent card formats and sizes the associated deck"""
	def __init__(self, *args, **kwargs):
		"""kwargs: deck, card_size, paper_size, orientation, print_path
		if card_size is present I have to join the elements of the deck following the premises"""
		self.printer = QPrinter(QPrinter.HighResolution)
		self.printer.setOutputFormat(QPrinter.PdfFormat)
		self.printer.setOrientation(getattr(QPrinter, kwargs["orientation"]))
		self.printer.setOutputFileName(kwargs["print_path"])
		self.printer.setPaperSize(getattr(QPrinter, kwargs["paper_size"]))

		self.paint = QPainter()

		self.deck = kwargs["deck"]

	def print_page(self, main_window):
		main_window.preview_view.render(self.paint)

	def begin(self):
		self.paint.begin(self.printer)

	def end(self):
		self.paint.end()

	def print_all(self, main_window):
		self.begin()
		for i in range(len(self.deck)):
			main_window.__preview__(i)
			self.print_page(main_window)
			if i < len(self.deck)-1:
				self.printer.newPage()
		self.end()

################## OLD #####################

class MainWindow(QMainWindow, Central):

	def __init__(self):
		QMainWindow.__init__(self)
		Central.__init__(self)
		self.setupUi(self)
		#self.readSettings()
		self.show()
		self.init_signals()
		self.handler_reset()

	def handler_reset(self):
		self.deck = Deck([])
		self.fichero_edit.setText("")
		self.scene = QGraphicsScene()
		self.preview_view.setScene(self.scene)
		self.preview_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.preview_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.preview_view.show()
		self.say("Ready")
		self.percent(0)

	def init_signals(self):
		self.elegir_boton.clicked.connect(self.handler_open_files)
		self.dividir_boton.clicked.connect(self.handler_split)
		self.unir_boton.clicked.connect(self.handler_join)
		self.preview_slider.valueChanged.connect(self.__preview__)
		self.borrar_boton.clicked.connect(self.handler_delete_card)
		self.negro_boton.clicked.connect(self.handler_black_borders)
		self.blanco_boton.clicked.connect(self.handler_white_borders)
		self.quitar_boton.clicked.connect(self.handler_delete_borders)
		self.guardar_como_boton.clicked.connect(self.handler_save_as)
		self.auto_boton.clicked.connect(self.handler_trim)
		self.top_crop.clicked.connect(self.handler_crop_top)
		self.right_crop.clicked.connect(self.handler_crop_right)
		self.bottom_crop.clicked.connect(self.handler_crop_bottom)
		self.left_crop.clicked.connect(self.handler_crop_left)
		self.all_crop.clicked.connect(self.handler_crop_all)
		self.reset_boton.clicked.connect(self.handler_reset)

	def all_selected(self):
		return self.todas_radio.isChecked()

	def handler_crop_top(self):
		px = self.crop_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.crop(top=px, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].crop(top=px)
		self.preview()

	def handler_crop_right(self):
		px = self.crop_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.crop(right=px, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].crop(right=px)
		self.preview()

	def handler_crop_bottom(self):
		px = self.crop_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.crop(bottom=px, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].crop(bottom=px)
		self.preview()

	def handler_crop_left(self):
		px = self.crop_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.crop(left=px, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].crop(left=px)
		self.preview()

	def handler_crop_all(self):
		px = self.crop_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.crop(top=px, bottom=px, left=px, right=px, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].crop(top=px, left=px, right=px, bottom=px)
		self.preview()

	def handler_delete_borders(self):
		if self.all_selected():
			self.reset_percent()
			self.deck.del_borders(call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].del_border()
		self.preview()

	def handler_trim(self):
		fuzz = self.umbral_spin_2.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.trim(fuzz, call=self.next_percent)
			self.complete_percent()
		else:
			self.deck[self.preview_slider.value()].trim(fuzz)
		self.preview()

	def handler_split(self):
		n = self.n_spin_2.value()
		m = self.m_spin_2.value()
		sep = self.sep_spin.value()
		if self.all_selected():
			self.reset_percent()
			self.deck.split(n, m, sep, call=self.next_percent)
			self.complete_percent()
		else:
			card = self.deck.del_card(self.preview_slider.value())
			self.deck.extend(card.split(n, m, sep))
		self.preview(0)
		self.say("Splited")

	def handler_join(self):
		n = self.n_spin_2.value()
		m = self.m_spin_2.value()
		sep = self.sep_spin.value()
		self.reset_percent()
		self.deck.join(n, m, sep, call=self.next_percent)
		self.complete_percent()
		self.preview(0)
		self.say("Merged")

	def handler_open_files(self):
		def getFiles():
			files = QFileDialog.getOpenFileNames(self, "Elige uno o mas ficheros", "./", "Images (*.png *.jpg);; PDF (*.pdf)")
			return files

		files = getFiles()
		if len(files) < 1:
			return
		prev = str(self.fichero_edit.text())
		names = ""
		if prev != "":
			names = prev + ", "
		names += ", ".join([str(el)[str(el).rfind("/")+1:] for el in files])
		self.fichero_edit.setText(names)
		self.reset_percent()
		for file in files:
			self.deck.load(file)
			self.next_percent(files)
		self.complete_percent()
		self.preview(0)
		self.say("Loaded")

	def handler_save_as(self):
		self.percent(0)
		name = QFileDialog.getSaveFileName(self, "Save as", "./")
		format = str(self.format_combo.currentText())
		card_size = str(self.card_size_combo.currentText())
		orientation = str(self.orientation_combo.currentText())
		paper_size = str(self.paper_size_combo.currentText())
		if format == "Separated images":
			num = 1
			self.reset_percent()
			for c in self.deck:
				c.save_as("".join([str(name),str(num),".",c.img.format.lower()]))
				self.next_percent()
				num += 1
			self.complete_percent()
		elif format == "Pdf from images":
			self.percent(50)
			p = Printer(deck = self.deck, card_size = str(self.card_size_combo.currentText()),
					orientation = str(self.orientation_combo.currentText()),
					paper_size = str(self.paper_size_combo.currentText()),
					print_path = str(name) + ".pdf")
			#begin printing
			#loop
				#make image(composite) and print it
				#next page
			#end printing
			pass
		elif format == "Pdf from grid":
			p = Printer(deck = self.deck, orientation = str(self.orientation_combo.currentText()),
					paper_size = str(self.paper_size_combo.currentText()),
					print_path = str(name) + ".pdf")
			p.print_all(self)
			#begin printing
			#loop
				#print image
				#next page
			#end printing
			pass
		self.percent(100)
		self.say("Save Completed")

	def handler_delete_card(self):
		num = self.preview_slider.value()
		self.deck.del_card(num)
		self.say("Card deleted")
		if num < len(self.deck):
			self.preview(num)
		else:
			self.preview(-1)

	def handler_black_borders(self):
		wide = self.border_spin.value()
		self.reset_percent()
		self.deck.borders(Border.black, wide, call=self.next_percent)
		self.complete_percent()
		self.preview()

	def handler_white_borders(self):
		wide = self.border_spin.value()
		self.reset_percent()
		self.deck.borders(Border.white, wide, call=self.next_percent)
		self.complete_percent()
		self.preview()

	def say(self, text):
		self.msg_label.setText(text)

	def percent(self, num):
		self.progress_bar.setValue(num)

	def reset_percent(self):
		self.percent(0)

	def next_percent(self,l=None):
		lon = self.deck if l is None else l
		self.percent(self.progress_bar.value()+100/len(lon))

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
		try:
			self.scene.clear()
			pm = self.scene.addPixmap(self.deck[num].pixmap())
			self.preview_view.fitInView(pm)
		except:
			self.scene.clear()
			pm = self.scene.addText("Image not available")
			self.preview_view.fitInView(pm)

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
