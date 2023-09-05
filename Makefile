# Makefile for Python project

# Variables
PYTHON := python3
PIP := pip3
PYINSTALLER := pyinstaller

BIN_SRC_DIR = ./dist
BIN_DEST_DIR = /usr/bin


SERVICE_DEST_DIR = /etc/systemd/system

# Name of the binary
BINARY_NAME = timeflip-tracker
SERVICE_NAME = timeflip-tracker.service

# Targets
.PHONY: all install test clean

all: build

build:
	$(PIP) install -r requirements.txt
	PYTHONPATH=env/lib/python3.11/site-packages/ pyinstaller --onefile --collect-all pytimefliplib timeflip-tracker.py

install:
    install -m 755 $(BIN_SRC_DIR)/$(BINARY_NAME) $(BIN_DEST_DIR)
    install -m 644 $(SERVICE_NAME) $(SERVICE_DEST_DIR)

    systemctl daemon-reload
	systemctl enable $(SERVICE_NAME)
    systemctl start $(SERVICE_NAME)

uninstall:
    systemctl stop $(SERVICE_NAME)
    systemctl disable $(SERVICE_NAME)

    rm -f $(BIN_DEST_DIR)/$(BINARY_NAME)
    rm -f $(SERVICE_DEST_DIR)/$(SERVICE_NAME)

    systemctl daemon-reload

clean:
	rm -rf __pycache__