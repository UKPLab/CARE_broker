#!make
include .env  #default env
ifdef ENV
	include .env.${ENV}
endif
export

.PHONY: default
default: help

.PHONY: help
help:
	@echo "make clean             	Delete development files"
	@echo "make guard             	Start guard"
	@echo "make scrub             	Scrub database"
	@echo "make init              	Initialize keys"
	@echo "make stress            	Run stress test"
	@echo "make broker              Start broker"
	@echo "make dev               	Start broker in development environment"
	@echo "make docker		  	    Start docker images for local development"
	@echo "make test				Run tests"
	@echo "make doc 			 	Generate documentation"
	@echo "make build      			Build all docker images - complete environment"
	@echo "make env_create			Create a virtual environment"
	@echo "make env_activate		Activate the virtual environment"
	@echo "make env_update			Update the virtual environment"

.PHONY: init
init:
	openssl genrsa -out private_key.pem 1024
	python3 client.py broker init || echo "IGNORING ERROR"

.PHONY: scrub
scrub:
	python3 client.py broker scrub

.PHONY: guard
guard:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 ./main.py

.PHONY: docker
docker:
	docker compose -f docker-compose.yml -f docker-dev.yml up arangodb

.PHONY: dev
dev:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 ./broker/app.py --dev

.PHONY: test
test:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 -u -m unittest test.test_broker.TestBroker


.PHONY: test_all
test_all:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 -m unittest discover test

.PHONY: stress
stress:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 -u -m unittest test.test_broker.TestBroker.stressTest

.PHONY: test-cli
test-cli:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 -u -m unittest test.test_cli.TestCLI

.PHONY: test-build
test-build:
	docker exec nlp_api_main-broker-1 python3 -u -m unittest test.test_broker.TestBroker

.PHONY: test-build-dev
test-build-dev:
	docker exec nlp_api_dev-broker-1 python3 -u -m unittest test.test_broker.TestBroker

.PHONY: test-stress
test-stress:
	docker exec nlp_api_main-broker-1 python3 -u -m unittest test.test_broker.TestBroker.stressTest
	docker cp nlp_api_main-broker-1:/tmp/stress_results.csv ./test/stress_results.csv

.PHONY: test-stress-dev
test-stress-dev:
	docker exec nlp_api_dev-broker-1 python3 -u -m unittest test.test_broker.TestBroker.stressTest
	docker cp nlp_api_dev-broker-1:/tmp/stress_results.csv ./test/stress_results.csv

.PHONY: broker
broker:
	export PYTHONPATH="${PYTHONPATH}:${CURDIR}" && python3 ./broker/app.py

.PHONY: build
build:
	docker compose -f docker-compose.yml -p "nlp_api_main" up --build -d

.PHONY: build-dev
build-dev:
	docker compose -f docker-compose.yml -p "nlp_api_dev" up --build -d

.PHONY: build-dev-clean
build-dev-clean:
	docker compose -p "nlp_api_dev" rm -f -s -v
	docker network rm nlp_api_dev_default || echo "IGNORING ERROR"

.PHONY: build-clean
build-clean: clean
	docker compose -p "nlp_api_main" rm -f -s -v
	docker network rm nlp_api_main_default || echo "IGNORING ERROR"

.PHONY: clean
clean:
	docker compose rm -f -s -v
	docker network rm nlp_api_default || echo "IGNORING ERROR"

.PHONY: env_create
env_create:
	conda env create -f environment.yaml

.PHONY: env_activate
env_activate:
	conda activate nlp_api

.PHONY: env_update
env_update:
	conda env update --file environment.yaml --name nlp_api --prune

.PHONY: doc
doc: doc_asyncapi doc_sphinx

.PHONY: clean_doc
clean_doc:
	cd ./docs && make clean
ifeq ($(OS),Windows_NT)
	rmdir /S /Q docs\docs
else
	rm -rf docs/docs
endif

.PHONY: doc_asyncapi
doc_asyncapi:
	docker run --rm -v ${CURDIR}/docs/api.yml:/app/api.yml -v ${CURDIR}/docs/html:/app/output asyncapi/generator:1.15.5 --force-write -o ./output api.yml @asyncapi/html-template

.PHONY: doc_sphinx
doc_sphinx:
	docker compose -f docker-compose.yml build docs_sphinx
	docker run --rm -v ${CURDIR}/docs:/docs broker_docs_sphinx make html


