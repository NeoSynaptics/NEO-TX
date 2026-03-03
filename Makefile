.PHONY: install dev test lock server

# Install core dependencies
install:
	pip install -e .

# Install with all optional deps + dev tools
dev:
	pip install -e ".[all,dev]"

# Run tests
test:
	pytest tests/ -v

# Generate pinned dependency lockfile
lock:
	pip-compile pyproject.toml -o requirements-lock.txt --strip-extras

# Run NEO-TX server
server:
	uvicorn neotx.server:app --host 127.0.0.1 --port 8100 --reload
