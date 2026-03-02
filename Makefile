.PHONY: install dev shadow-setup shadow-start shadow-stop shadow-health test demo

# Install core dependencies
install:
	pip install -e .

# Install with all optional deps + dev tools
dev:
	pip install -e ".[all,dev]"

# WSL2 shadow desktop setup
shadow-setup:
	wsl -d Ubuntu -- bash -c "cd /mnt/c/Users/info/GitHub/NEO-TX && bash wsl/setup.sh"

# Start shadow desktop
shadow-start:
	wsl -d Ubuntu -- bash -c "cd /mnt/c/Users/info/GitHub/NEO-TX && bash wsl/start_shadow.sh"

# Stop shadow desktop
shadow-stop:
	wsl -d Ubuntu -- bash -c "cd /mnt/c/Users/info/GitHub/NEO-TX && bash wsl/stop_shadow.sh"

# Check shadow desktop health
shadow-health:
	wsl -d Ubuntu -- bash -c "cd /mnt/c/Users/info/GitHub/NEO-TX && bash wsl/health_check.sh"

# Run tests
test:
	pytest tests/ -v

# Run Phase 1 demo
demo:
	python scripts/demo.py

# Run NEO-TX server
server:
	uvicorn neotx.server:app --host 127.0.0.1 --port 8100 --reload
