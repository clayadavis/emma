library.zip:
	cd ..; python2.4 setup.py bdist
	tar -xzf ../dist/$(shell /bin/ls ../dist -1 -rt | tail -1) ./usr/lib/python2.4/site-packages/emmalib
	find ./usr/ -iname "*.pyc" | while read file; do echo $$file; mv $$file library/encodings; done
	-rm -rf ./usr
	cd ./library; zip ../dist/library.zip *
	