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
from PyQt4.QtCore import QSettings, pyqtSlot, Qt, QRectF

from card import Card, Border
from deck import Deck

class Printer(object):
	"""For printing in diferent card formats and sizes the associated deck, be it to the screen or pdfs or image files"""

	card_sizes = {"Jumbo":(3.5,5.5), "Tarot":(2.75,4.75), "Square":(3.5,3.5), "Poker":(2.5,3.5),
			 "Bridge":(2.25,3.5), "Biz":(2,3.5), "Mini":(1.75,2.5), "Micro":(1.25,1.75)}
	paper_sizes = {"A0":(),"A1":(),"A2":(),"A3":(),"A4":(8.3,11.7)}

	def __init__(self):
		self.deck = None
		self.scene = QGraphicsScene()
		self.orientation = getattr(QPrinter, "Portrait")
		self.path = "output.pdf"
		self.paper = getattr(QPrinter, "A4")
		self.card_size = Printer.card_sizes["Poker"]

	def config(self, *args, **kwargs):
		"""kwargs: deck, card_size, paper_size, orientation, print_path
		if card_size is present I have to join the elements of the deck following the premises"""
		if "orientation" in kwargs:
			self.orientation = kwargs["orientation"]
		if "card_size" in kwargs:
			self.card_size = Printer.card_sizes[kwargs["card_size"][:kwargs["card_size"].find(" ")]]
		if "print_path" in kwargs:
			self.path = kwargs["print_path"]
		if "paper_size" in kwargs:
			self.paper = kwargs["paper_size"]
		if "deck" in kwargs:
			self.deck = kwargs["deck"]

	def print_grid(self):
		printer = QPrinter(QPrinter.HighResolution)
		printer.setOutputFormat(QPrinter.PdfFormat)
		printer.setOrientation(getattr(QPrinter, self.orientation))
		printer.setOutputFileName(self.path)
		printer.setPaperSize(getatte(QPrinter, self.paper))
		if self.deck is not None:
			with QPainter(printer) as paint:
				first = True
				for c in self.deck:
					if not first:
						printer.newPage()
					first = False
					self.preview_card(c)
					self.scene.render(paint)

	def max_cards(self):
		"""Taking in count the card_size, paper_size and orientation returns the max number of cards per page"""
		if self.orientation == "Portrait":
			pw = self.paper_sizes[self.paper][0]
			ph = self.paper_sizes[self.paper][1]
		else:
			ph = self.paper_sizes[self.paper][0]
			pw = self.paper_sizes[self.paper][1]
		return int((pw//self.card_size[0])*(ph//self.card_size[1]))

	def print_pdf(self):
		print self.max_cards()
		return
		printer = QPrinter(QPrinter.HighResolution)
		printer.setOutputFormat(QPrinter.PdfFormat)
		printer.setOrientation(self.orientation)
		printer.setOutputFileName(self.path)
		printer.setPaperSize(self.paper)
		if self.deck is not None:
			with QPainter(printer) as paint:
				first = True
				for c in self.deck:
					if not first:
						printer.newPage()
					first = False
					self.preview_card(c)
					self.scene.render(paint, target=QRectF(0,0,self.card_size[0]*printer.resolution(), self.card_size[1]*printer.resolution()))

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
		return ret
