all: sdist

sdist:
	python setup.py sdist 

clean:
	-sudo rm -rf build build-stamp debian/emma debian/*.debhelper
	sudo find ./emmalib -iname "*.py[co]" -exec rm "{}" ";"
