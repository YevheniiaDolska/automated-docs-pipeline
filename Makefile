.PHONY: install validate validate-minimal validate-full test docs-serve build smoke gaps api-sandbox api-sandbox-stop clean-reports configurator detect-generator build-mkdocs build-docusaurus serve-mkdocs serve-docusaurus convert-to-docusaurus convert-to-mkdocs

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

api-sandbox:
	npm run api:sandbox:mock

api-sandbox-stop:
	npm run api:sandbox:stop

build:
	python3 scripts/run_generator.py build

build-mkdocs:
	mkdocs build --strict

build-docusaurus:
	npx docusaurus build

docs-serve:
	python3 scripts/run_generator.py serve

serve-mkdocs:
	mkdocs serve

serve-docusaurus:
	npx docusaurus start

detect-generator:
	python3 scripts/run_generator.py detect

convert-to-docusaurus:
	python3 scripts/markdown_converter.py to-docusaurus docs/

convert-to-mkdocs:
	python3 scripts/markdown_converter.py to-mkdocs docs/

configurator:
	python3 scripts/generate_configurator.py

clean-reports:
	rm -f reports/*.json reports/*.md reports/*.html reports/*.csv reports/*.xlsx
