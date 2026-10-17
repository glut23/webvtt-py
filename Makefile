build:
	rm -rf dist
	mkdir dist
	python setup.py sdist bdist_wheel
	twine check dist/*

release_test: build
	twine upload -r testpypi dist/*

release: build
	twine upload dist/*

man:
	sphinx-build -q -E -b man docs/source docs/build/man
	mkdir -p man
	cp docs/build/man/webvtt.1 man/webvtt.1

.PHONY: build release_test release man