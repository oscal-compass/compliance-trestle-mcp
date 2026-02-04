.PHONY: test
test: test-unit test-e2e
	@echo "Run All Tests"

.PHONY: test-unit
test-unit:
	@echo "Running Unit Tests"
	@pytest tests/unit

.PHONY: test-e2e
test-e2e:
	@echo "Running End-to-end Tests"
	@pytest tests/e2e

.PHONY: format
format:
	@echo "Format codes and organize imports"
	@black .
	@isort .

.PHONY: lint
lint:
	@echo "Linting with ruff check"
	@ruff check .
	
# Install detect-secret globally
.PHONY: install-detect-secret
install-detect-descret:
	pip install detect-secrets@git+https://github.com/ibm/detect-secrets.git@0.13.1+ibm.64.dss#egg=detect-secrets
