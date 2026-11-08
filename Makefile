help: ## Show this help
	@awk -F':.*## ' '/^[a-z_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean: ## Remove the generated files, including dist
	rm -rf build dist docs/build *.egg-info .tox .mypy_cache .pytest_cache .hypothesis .coverage coverage.xml

codestyle: ## Check the code style and types
	tox -e codestyle

test: ## Run the tests
	tox -e py

coverage: test ## Run the tests, print the coverage report and write coverage.xml
	tox -e coverage

coverage-report: test ## Run the tests and print the coverage report
	tox exec -e coverage -- coverage report

coverage-xml: test ## Run the tests and write coverage.xml
	tox exec -e coverage -- coverage xml

man: ## Regenerate the man page
	tox -e man

build: ## Build the packages in dist from a clean state and check them
	tox -e build

release_test: build ## Build and upload the packages to TestPyPI
	tox -e release -- -r testpypi dist/*

release: build ## Build and upload the packages to PyPI
	tox -e release -- dist/*

.PHONY: help clean codestyle test coverage coverage-report coverage-xml man build release_test release
