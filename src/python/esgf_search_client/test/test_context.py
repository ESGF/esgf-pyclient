"""
Test the SearchContext class

"""

from esgf_search.connection import SearchConnection

from .config import TEST_SERVICE

def test_context_freetext():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(query="temperature")

    assert context.freetext_constraint == "temperature"

def test_context_facets1():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='cmip5')

    assert context.facet_constraints['project'] == 'cmip5'
    
def test_context_facets1():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5')

    context2 = context.constrain(model="IPSL-CM5A-LR")
    assert context2.facet_constraints['project'] == 'CMIP5'
    assert context2.facet_constraints['model'] == 'IPSL-CM5A-LR'

def test_context_facets3():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    context2 = context.constrain(model="IPSL-CM5A-LR")

    response = context2.search()
    doc = response['response']['docs'][0]

    assert doc['project'] == ['CMIP5']
    assert doc['model'] == ['IPSL-CM5A-LR']
