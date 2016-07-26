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

from copy import deepcopy as deep_copy

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
		"""*obj* to keep track"""
		self.obj = obj
		self.states = [State(obj, "Initial state")]
		self.current_state = 1
		self.length = 50

	def track(self, msg="Default message"):
		"""Add a new state to the states list, just after the current state"""
		while self.current_state < len(self.states):
			self.states.pop()
		if len(self.states) == self.length:
			self.states.pop(0)
			self.current.state -= 1
		self.states.append(State(self.obj, msg))
		self.current_state += 1

	def undo(self):
		"""Undo one action"""
		if self.current_state > 1:
			self.current_state -= 1
			self.reload_obj()

	def redo(self):
		"""Redo one action"""
		if self.current_state < len(self.states):
			self.current_state += 1
			self.reload_obj()

	def reload_obj(self):
		"""Changes obj to the current state if method set is found"""
		self.obj.set(self.get_current())

	def msg_current(self):
		return self.states[self.current_state - 1].get_msg()

	def get_current(self):
		return self.states[self.current_state - 1].get_obj()

class Command(object):
	"""To easily instance History-able objects"""
	def __init__(self):
		self.history = History(self)

	def set(self, new):
		"""Redefine this method in the new class to work with this object"""
		raise NotImplementedError()

	def register(self, msg):
		self.history.track(msg)

	def undo(self):
		self.history.undo()

	def redo(self):
		self.history.redo()

def keep_state(msg):
	"""Functions decorated with keep_state will add the state to History after commiting changes"""
	def deco(func):
		def wrapper(self, *args, **kwargs):
			regis = False
			if "register" in kwargs:
				regis = kwargs["register"]
				del kwargs["register"]
			res = func(self, *args, **kwargs)
			if regis:
				self.register(msg)
			return res
		return wrapper
	return deco
