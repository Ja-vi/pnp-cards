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

#Graphics
from PyQt4.QtGui import QImage, QPixmap

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

	def format(self, fmt=None):
		if fmt is None:
			return self.img.format.lower()
		else:
			self.img.format = fmt

	def resize(self, width, height):
		"""Resize this card to (width, height) inches"""
		res = self.img.resolution
		print res
		self.img.resize(int(width*res[0]), int(height*res[1]))
		print self.img.resolution

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

	def clone(self):
		c = Card(image=self.img.clone())
		c.border = self.border
		return c

	def pixmap(self):
		"""Update and returns the pixmap (QPixmap) of the contained image"""
		if self.changed:
			self._pixmap = QPixmap(QImage.fromData(self.img.make_blob(), self.img.format))
			self.changed = False
		return self._pixmap
