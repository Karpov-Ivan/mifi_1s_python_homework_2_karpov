UV ?= uv

.PHONY: install run lint

install:
	$(UV) sync

run:
	$(UV) run database

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
