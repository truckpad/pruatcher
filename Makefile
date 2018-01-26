DESCRIPTION=GitHub PRUatcher

ACCOUNT_ID?=218817830640
REGION_NAME?=us-west-2
ROLE?=lambda-s3

ENV?=prod
EVENT_NAME?=every_weekday
FUNCTION_NAME?=pruatcher
MEMORY_SIZE=128
TIMEOUT?=10

EVENT_SOURCE_ARN=arn:aws:events:$(REGION_NAME):$(ACCOUNT_ID):rule/$(EVENT_NAME)
FUNCTION_ARN=arn:aws:lambda:$(REGION_NAME):$(ACCOUNT_ID):function:$(ENV)-$(FUNCTION_NAME)
ROLE_ARN=arn:aws:iam::$(ACCOUNT_ID):role/$(ROLE)
VERSION=$(shell python setup.py -V)


all:
	$(MAKE) clean
	$(MAKE) build publish


virtualenv:
	if [ ! -d venv ]; then virtualenv venv; fi
	if [ ! -d venv/bin/aws ]; then venv/bin/pip install --upgrade awscli; fi
	venv/bin/pip install --upgrade -r requirements.txt


build: virtualenv
	LC_ALL=en_US.UTF-8 venv/bin/python setup.py sdist --formats=gztar
	mkdir build
	# cp aws_lambda.py build/ && cp -R -v truckpad build/
	cp *.cfg *.py *.json *.md *.txt build/
	- cat requirements.txt | grep -v '^boto' > build/requirements.txt && venv/bin/pip install --upgrade --no-compile -r build/requirements.txt -t build/
	rm -rf build/tests/
	cd build/ ; zip -9 -r ../dist/truckpad-$(FUNCTION_NAME)-$(VERSION)-lambda.zip . ; cd .. && rm -rf build


publish: build
	venv/bin/aws lambda create-function \
		--region $(REGION_NAME) \
		--function-name $(FUNCTION_ARN) \
		--runtime python2.7 \
		--role $(ROLE_ARN) \
		--handler pruatcher.lambda_handler \
		--description "$(DESCRIPTION)" \
		--timeout $(TIMEOUT) \
		--memory-size $(MEMORY_SIZE) \
		--zip-file fileb://dist/truckpad-$(FUNCTION_NAME)-$(VERSION)-lambda.zip
	venv/bin/aws lambda add-permission \
		--region $(REGION_NAME) \
		--function-name $(FUNCTION_ARN) \
		--source-arn $(EVENT_SOURCE_ARN) \
		--principal events.amazonaws.com \
		--action 'lambda:InvokeFunction' \
		--statement-id '$(FUNCTION_NAME)'
	venv/bin/aws events put-targets \
		--region $(REGION_NAME) \
		--rule $(EVENT_NAME) \
		--targets '{"Id" : "1", "Arn": "$(FUNCTION_ARN)"}'


update: build
	venv/bin/aws lambda update-function-code \
		--region $(REGION_NAME) \
		--function-name $(FUNCTION_ARN) \
		--zip-file fileb://dist/truckpad-$(FUNCTION_NAME)-$(VERSION)-lambda.zip
	venv/bin/aws lambda publish-version \
		--region $(REGION_NAME) \
		--function-name $(FUNCTION_ARN) \
		--description "Package $(FUNCTION_NAME) version $(VERSION)"


destroy:
	venv/bin/aws lambda delete-function \
		--region $(REGION_NAME) \
		--function-name $(FUNCTION_ARN)


clean:
	rm -rf build/
	rm -f dist/*
