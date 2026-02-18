.PHONY: install validate validate-minimal validate-full test docs-serve build smoke gaps clean-reports

install:
	python3 -m pip install -r requirements.txt
	npm install

validate-minimal:
	npm run lint:md
	npm run lint:frontmatter
	npm run lint:geo
	npm run lint:examples-smoke

validate-full: validate-minimal
	npm run docs-ops:e2e
	npm run docs-ops:golden
	npm run docs-ops:test-suite
	python3 test_pipeline.py

validate: validate-minimal

test:
	npm run docs-ops:test-suite
	npm run docs-ops:e2e
	npm run docs-ops:golden

smoke:
	npm run lint:examples-smoke

gaps:
	npm run gaps

build:
	npm run build

docs-serve:
	npm run serve

clean-reports:
	rm -f reports/*.json reports/*.md reports/*.html reports/*.csv reports/*.xlsx
