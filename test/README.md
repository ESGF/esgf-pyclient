In order to run the tests:

 nosetests --tests=test --logging-level=DEBUG # run all
 nosetests --tests=test/test_context.py:test_response_from_bad_parameter --logging-level=DEBUG # run just one

