

all: ui exe

exe:
	python pnp-cards.py

ui: central.ui
	pyuic4 central.ui -o window.py
