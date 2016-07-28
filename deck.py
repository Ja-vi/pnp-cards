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

#Image manipulation
from wand.image import Image

from card import Card, Border

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

