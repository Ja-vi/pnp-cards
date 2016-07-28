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
from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QPrinter, QGraphicsScene, QGraphicsView, QPainter
from PyQt4.QtCore import QSettings, pyqtSlot, Qt
from window import Ui_Form as Central

from card import Card, Border
from deck import Deck
from printer import Printer

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
