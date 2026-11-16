.PHONY: install test lint smoke audit clean

install:
	pip install -e ".[analysis,dev]"

test:
	pytest tests/ -q

lint:
	ruff check src/ tests/ scripts/

smoke:
	vyapti-smoke

audit:
	python scripts/secret_scan.py .
	python scripts/audit_taxonomy.py
	python scripts/audit_contamination.py --self-check

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
