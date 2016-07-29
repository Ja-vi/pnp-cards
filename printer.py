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
	paper_sizes = {"A0":(33.1,46.8), "A1":(23.4,33.1), "A2":(16.5,23.4), "A3":(11.7,16.5),
				   "A4":(8.3,11.7), "A5":(5.8,8.3), "A6":(4.1,5.8)}

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
		if self.deck is not None:
			#Setting the printer
			printer = QPrinter(QPrinter.HighResolution)
			printer.setOutputFormat(QPrinter.PdfFormat)
			printer.setOrientation(getattr(QPrinter, self.orientation))
			printer.setOutputFileName(self.path)
			printer.setPaperSize(getattr(QPrinter, self.paper))
			#Start printing
			with QPainter(printer) as paint:
				first = True
				for c in self.deck:
					if not first:
						printer.newPage()
					first = False
					self.preview_card(c)
					self.scene.render(paint)

	def max_cards(self):
		"""Taking in count the card_size, paper_size returns the max number of cards per page, horientation and margins"""
		port = {}
		port["orientation"] = "Portrait"
		pw = self.paper_sizes[self.paper][0]
		ph = self.paper_sizes[self.paper][1]
		port["horizontal"] = int(pw//self.card_size[0])
		port["vertical"] = int(ph//self.card_size[1])
		port["max"] = port["horizontal"] * port["vertical"]
		port["margin_horizontal"] = (pw % self.card_size[0]) / 2.0
		port["margin_vertical"] = (ph % self.card_size[1]) / 2.0
		land = {}
		land["orientation"] = "Landscape"
		pw = self.paper_sizes[self.paper][1]
		ph = self.paper_sizes[self.paper][0]
		land["horizontal"] = int(pw//self.card_size[0])
		land["vertical"] = int(ph//self.card_size[1])
		land["max"] = land["horizontal"] * land["vertical"]
		land["margin_horizontal"] = (pw % self.card_size[0]) / 2.0
		land["margin_vertical"] = (ph % self.card_size[1]) / 2.0
		if land["max"] > port["max"]:
			return land
		else:
			return port

	def print_pdf(self):
		if self.deck is not None:
			#Setting the printer
			printer = QPrinter(QPrinter.HighResolution)
			printer.setOutputFormat(QPrinter.PdfFormat)
			printer.setOrientation(getattr(QPrinter, "Portrait"))
			printer.setOutputFileName(self.path)
			printer.setPaperSize(getattr(QPrinter, self.paper))
			printer.setFullPage(True)
			guide = self.max_cards()
			printer.setOrientation(getattr(QPrinter, guide["orientation"]))
			print guide, self.card_size
			#Start printing
			with QPainter(printer) as paint:
				ind = 0
				resol = printer.resolution()
				for c in self.deck:
					with c as clon:
						resclon = clon.resize(self.card_size[0], self.card_size[1])
						if ind == guide["max"]:
							printer.newPage()
							ind = 0

						col = ind % guide["vertical"]
						fil = ind // guide["horizontal"]
						print ind, fil, col
						target = QRectF((col)*self.card_size[0]*resol, (fil)*self.card_size[1]*resol,
									self.card_size[0]*resol, self.card_size[1]*resol)

						self.preview_card(clon)
						self.scene.render(paint, target=target)#, source=QRectF(0,0,clon.width(),clon.height()))
						ind += 1

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
