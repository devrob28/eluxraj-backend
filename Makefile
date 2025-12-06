.PHONY: dev test lint format migrate install clean

dev:
	./run.sh dev

test:
	./run.sh test

lint:
	./run.sh lint

format:
	./run.sh format

migrate:
	./run.sh migrate

install:
	./run.sh install

db:
	./run.sh db

stop:
	./run.sh stop

clean:
	./run.sh clean

docker:
	./run.sh docker
