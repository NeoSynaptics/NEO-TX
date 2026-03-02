.PHONY: install dev test server

# Install core dependencies
install:
	pip install -e .

# Install with all optional deps + dev tools
dev:
	pip install -e ".[all,dev]"

# Run tests
test:
	pytest tests/ -v

# Run NEO-TX server
server:
	uvicorn neotx.server:app --host 127.0.0.1 --port 8100 --reload
