CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra

all: helper/lenovo-vantage-helper

helper/lenovo-vantage-helper: helper/helper.c
	$(CC) $(CFLAGS) $< -o $@

install: helper/lenovo-vantage-helper
	@sudo ./install.sh

uninstall:
	@sudo ./uninstall.sh

clean:
	rm -f helper/lenovo-vantage-helper

.PHONY: all install uninstall clean
