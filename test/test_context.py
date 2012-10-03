"""
Test the SearchContext class

"""

from pyesgf.search.connection import SearchConnection

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

def test_context_facets_multivalue():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5')

    context2 = context.constrain(model=['IPSL-CM5A-LR', 'IPSL-CM5A-MR'])
    assert context2.hit_count > 0
    
    assert context2.facet_constraints['project'] == 'CMIP5'
    assert context2.facet_constraints['model'] == ['IPSL-CM5A-LR', 'IPSL-CM5A-MR']

def test_context_facet_options():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR',
                               ensemble='r1i1p1', experiment='rcp60',
                               realm='seaIce'
        )

    assert context.get_facet_options().keys() == [
        'product', 'cf_standard_name', 'variable_long_name', 'cmor_table',
        'time_frequency', 'variable'
        ]
    


def test_context_facets3():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    context2 = context.constrain(model="IPSL-CM5A-LR")

    results = context2.search()
    result = results[0]

    assert result.json['project'] == ['CMIP5']
    assert result.json['model'] == ['IPSL-CM5A-LR']

def test_facet_count():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    context2 = context.constrain(model="IPSL-CM5A-LR")

    counts = context2.facet_counts
    assert counts['model'].keys() == ['IPSL-CM5A-LR']
    assert counts['project'].keys() == ['CMIP5']

def test_distrib():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    context = conn.new_context(project='CMIP5')
    count1 = context.hit_count

    conn2 = SearchConnection(TEST_SERVICE, distrib=True)
    context = conn2.new_context(project='CMIP5')
    count2 = context.hit_count

    assert count1 < count2

def test_constrain():
    conn = SearchConnection(TEST_SERVICE)
    
    context = conn.new_context(project='CMIP5')
    count1 = context.hit_count
    context = context.constrain(model="IPSL-CM5A-LR")
    count2 = context.hit_count

    assert count1 > count2
