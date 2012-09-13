"""
Test the SearchContext class

"""

from pyesgf.connection import SearchConnection

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

    results = context2.search()
    doc = results[0]

    assert doc['project'] == ['CMIP5']
    assert doc['model'] == ['IPSL-CM5A-LR']

def test_facet_count():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    context2 = context.constrain(model="IPSL-CM5A-LR")

    counts = context2.facet_counts
    assert counts['model'].keys() == ['IPSL-CM5A-LR']
    assert counts['project'].keys() == ['CMIP5']

def test_distrib():
    conn = SearchConnection(TEST_SERVICE)

    context = conn.new_context(project='CMIP5')
    count1 = context.hit_count

    #!TODO: this breaks caching!
    conn.distrib = False
    count2 = context.hit_count

    assert count1 > count2

def test_constrain():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    count1 = context.hit_count
    context = context.constrain(model="IPSL-CM5A-LR")
    count2 = context.hit_count

    assert count1 > count2
