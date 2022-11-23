default: clean build

clean:
	rm -f ../autoinstall-desktop.md out.temp

build:
	./build_doc.py autoinstall-desktop.md.in ../autoinstall-desktop.md

test:
	./build_doc.py autoinstall-desktop.md.in out.temp
	diff -u ../autoinstall-desktop.md out.temp
