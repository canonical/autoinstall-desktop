default: clean build

clean:
	rm -f ../README.md out.temp

build:
	./build_doc.py README.md.in ../README.md

test:
	./build_doc.py README.md.in out.temp
	diff -u ../README.md out.temp
