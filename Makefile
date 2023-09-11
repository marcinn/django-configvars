.PHONY: package upload clean

env:
	python3 -m venv env
	@source env/bin/activate && pip install -U pip wheel twine build

package: env
	@rm -rf dist
	@mkdir dist
	@source env/bin/activate && python3 -m build

upload: package
	@source env/bin/activate && twine upload --verbose --skip-existing dist/*

clean:
	rm -rf env && rm -rf dist
