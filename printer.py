#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
Copyright 2016, Luis Javier Gonzalez (javi.gonzalez@zoho.com)

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
from PyQt4.QtGui import QFileDialog, QPrinter, QGraphicsScene, QGraphicsView, QPainter
from PyQt4.QtCore import QSettings, pyqtSlot, Qt

from card import Card, Border
from deck import Deck

class Printer(object):
	"""For printing in diferent card formats and sizes the associated deck, be it to the screen or pdfs or image files"""

	card_sizes = {"Jumbo":(3.5,5.5), "Tarot":(2.75,4.75), "Square":(3.5,3.5), "Poker":(2.5,3.5),
			 "Bridge":(2.25,3.5), "Biz":(2,3.5), "Mini":(1.75,2.5), "Micro":(1.25,1.75)}

	def __init__(self)
		self.deck = None
		self.printer = None
		self.scene = QGraphicsScene()
		self.orientation = getattr(QPrinter, "Portrait")
		self.path = "output.pdf"
		self.paper = getattr(QPrinter, "A4")
		self.card_size = Printer.card_sizes["Poker"]

	def config(self, *args, **kwargs):
		"""kwargs: deck, card_size, paper_size, orientation, print_path
		if card_size is present I have to join the elements of the deck following the premises"""
		if "orientation" in kwargs:
			self.orientation = getattr(QPrinter, kwargs["orientation"])
		if "card_size" in kwargs:
			self.card_size = Printer.card_sizes[kwargs["card_size"][:kwargs["card_size"].find(" ")]]
		if "print_path" in kwargs:
			self.path = kwargs["print_path"]
		if "paper_size" in kwargs:
			self.paper = getattr(QPrinter, kwargs["paper_size"])
		if "deck" in kwargs:
			self.deck = kwargs["deck"]

	def print_grid(self):
		self.printer = QPrinter(QPrinter.HighResolution)
		self.printer.setOutputFormat(QPrinter.PdfFormat)
		self.printer.setOrientation(self.orientation)
		self.printer.setOutputFileName(self.path)
		self.printer.setPaperSize(self.paper)
		if self.deck is not None:
			with QPainter() as paint:
				self.paint.begin(self.printer)
				first = True
				for c in self.deck:
					if not first:
						self.printer.newPage()
					first = False
					self.preview_card(c)
					self.scene.render(self.paint)
				self.paint.end()
		self.printer = None

	def print_pdf(self):
		self.printer = QPrinter(QPrinter.HighResolution)
		self.printer.setOutputFormat(QPrinter.PdfFormat)
		self.printer.setOrientation(self.orientation)
		self.printer.setOutputFileName(self.path)
		self.printer.setPaperSize(self.paper)
		resized = Deck([])
		for c in self.deck:
			resized.append(c.clone().resize(*self.card_size))
		if self.deck is not None:
			pass
		self.printer = None


	def print_images(self):
		if self.deck is not None:
			num = 1
			for c in self.deck:
				c.save_as("".join([str(self.path),str(num),".",c.format()]))
				num += 1

	def preview_card(self, card):
		try:
			self.scene.clear()
			ret = self.scene.addPixmap(card.pixmap())
		except:
			self.scene.clear()
			ret = self.scene.addText("Image not available")

################## OLD #####################

class MainWindow():

	def __init__(self):
		self.handler_reset()

	def handler_reset(self):
		self.printer = Printer()
		self.preview_view.setScene(self.printer.scene)
		self.preview_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.preview_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.preview_view.show()
		self.say("Ready")
		self.percent(0)

	def handler_save_as(self):
		self.percent(0)
		name = QFileDialog.getSaveFileName(self, "Save as", "./")
		format = str(self.format_combo.currentText())
		card_size = str(self.card_size_combo.currentText())
		orientation = str(self.orientation_combo.currentText())
		paper_size = str(self.paper_size_combo.currentText())
		if format == "Separated images":
			self.printer.config(deck = self.deck, print_path = str(name))
			self.printer.print_images()
		elif format == "Pdf from images":
			self.percent(50)
			self.printer.config(deck = self.deck, card_size = str(self.card_size_combo.currentText()),
					orientation = str(self.orientation_combo.currentText()),
					paper_size = str(self.paper_size_combo.currentText()),
					print_path = str(name) + ".pdf")
		elif format == "Pdf from grid":
			self.printer.config(deck = self.deck, orientation = str(self.orientation_combo.currentText()),
					paper_size = str(self.paper_size_combo.currentText()),
					print_path = str(name) + ".pdf")
			self.printer.print_grid()
		self.percent(100)
		self.say("Save Completed")

	def preview(self, num=None):
		ldeck = len(self.deck)
		self.preview_slider.setMaximum((ldeck-1) if ldeck > 0 else 0)
		num = self.preview_slider.value() if num is None else num
		pm = self.printer.preview_card(self.deck[num])
		self.preview_view.fitInView(pm)

