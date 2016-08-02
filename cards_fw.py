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

	@set_changed
	def resize(self, width, height, newres=300):
		"""Resize this card to (*width*, *height*) inches, with a resolution of *newres*"""
		print self.img.resolution, self.img.size, str(int(width*newres)) + "x" + str(int(height*newres)) + "!"
		self.img.transform(resize=str(int(width*newres)) + "x" + str(int(height*newres)) + "!")
		self.img.reset_coords()
		#self.img.resolution = (newres, newres)
		print self.img.resolution, self.img.size

		print("blob")
		self.img.make_blob("jpg")
		print("endblob")

		return newres

	def width(self):
		return self.img.size[0]

	def height(self):
		return self.img.size[1]

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

	@set_changed
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

	@set_changed
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
			self._pixmap = QPixmap(QImage.fromData(self.img.make_blob("jpg"), "jpg"))#self.img.format))
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

