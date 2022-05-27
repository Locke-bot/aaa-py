default: main

watch:
	cd build && pipenv run python src/watch/monitor.py

install:
	cd build && pipenv install

build: build/main.py
	cd build && pipenv run python main.py

build_local: build/main.py
	cd build && pipenv run python main.py --local

build_single: build/main.py
	cd build && pipenv run python main.py --single $(MAKE)

serve:
	cd build/website && pipenv run python -m http.server 8080

sentinel:
	${MAKE} -j4 serve watch

main: | install build serve

local: | build_local serve

.PHONY: build build_local install local main serve
