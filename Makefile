

all: ui exe

exe:
	python main.py

ui: central.ui
	pyuic4 central.ui -o window.py
