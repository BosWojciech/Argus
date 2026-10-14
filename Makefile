# Prefer uv's own Python builds (they include Tk); a python.org install works too.
export UV_PYTHON_PREFERENCE := managed
MIN_PYTHON := 3.13
INSTALL_HINT := install Python $(MIN_PYTHON) from https://www.python.org/downloads/ or run: uv python install $(MIN_PYTHON)

# Fail early with one readable line instead of a long uv/pip traceback.
ifneq ($(filter-out clean,$(or $(MAKECMDGOALS),install)),)
ifeq ($(shell command -v uv),)
$(error uv is not installed. Install it from https://docs.astral.sh/uv/ and run make install again)
endif
PYTHON := $(shell UV_PYTHON_PREFERENCE=$(UV_PYTHON_PREFERENCE) uv python find ">=$(MIN_PYTHON)" 2>/dev/null)
ifeq ($(PYTHON),)
$(error Python version is too old. Please $(INSTALL_HINT))
endif
ifeq ($(shell "$(PYTHON)" -c "import tkinter" 2>/dev/null && echo ok),)
$(error Python at $(PYTHON) has no Tk support, which the window needs. Please $(INSTALL_HINT))
endif
endif

.PHONY: install data run test clean

install: ## Create .venv and install dependencies
	@uv sync -q --python "$(PYTHON)" && echo "Installed. Start the app with: make run"

data: ## Download the latest open data (~150 MB, temporary) and rebuild db/argus.db
	uv run python scripts/build_data.py

run: ## Launch the desktop app
	@uv run argus

test: ## Run the test suite
	uv run pytest -q

clean: ## Remove the virtual environment and caches
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
