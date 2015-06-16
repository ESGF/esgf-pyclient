"""
Test the SearchContext class

"""

from pyesgf.search import SearchConnection, not_equals

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
    assert sorted(context2.facet_constraints.getall('model')) == ['IPSL-CM5A-LR', 'IPSL-CM5A-MR']

def test_context_facet_multivalue2():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5', model='IPSL-CM5A-MR')
    assert context.facet_constraints.getall('model') == ['IPSL-CM5A-MR']

    
    context2 = context.constrain(model=['IPSL-CM5A-MR', 'IPSL-CM5A-LR'])
    assert sorted(context2.facet_constraints.getall('model')) == ['IPSL-CM5A-LR', 'IPSL-CM5A-MR']


def test_context_facet_multivalue3():
    conn = SearchConnection(TEST_SERVICE)
    ctx = conn.new_context(project='CMIP5', query='humidity', experiment='rcp45')
    hits1 = ctx.hit_count
    assert hits1 > 0
    ctx2 = conn.new_context(project='CMIP5', query='humidity',
                           experiment=['rcp45','rcp85'])
    hits2 = ctx2.hit_count

    assert hits2 > hits1


def test_context_facet_options():
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR',
                               ensemble='r1i1p1', experiment='rcp60',
                               realm='seaIce')

    assert context.get_facet_options().keys() == ['data_node', 'cf_standard_name', 'variable_long_name', 
                               'cmor_table', 'time_frequency', 'variable']


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


def test_constrain_freetext():
    conn = SearchConnection(TEST_SERVICE)

    context = conn.new_context(project='CMIP5', query='humidity')
    assert context.freetext_constraint == 'humidity'

    context = context.constrain(experiment='historical')
    assert context.freetext_constraint == 'humidity'

def test_constrain_regression1():
    conn = SearchConnection(TEST_SERVICE)

    context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR')
    assert 'experiment' not in context.facet_constraints

    context2 = context.constrain(experiment='historical')
    assert 'experiment' not in context.facet_constraints

def test_negative_facet():
    conn = SearchConnection(TEST_SERVICE)

    context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR')
    hits1 = context.hit_count

    print context.facet_counts['experiment']

    context2 = context.constrain(experiment='historical')
    hits2 = context2.hit_count

    context3 = context.constrain(experiment=not_equals('historical'))
    hits3 = context3.hit_count


    assert hits1 == hits2 + hits3
    
def test_replica():
    # Test that we can exclude replicas
    # This tests assumes the test dataset is replicated
    conn = SearchConnection(TEST_SERVICE)

    context = conn.new_context(
        query='cmip5.output1.NIMR-KMA.HadGEM2-AO.rcp60.mon.atmos.Amon.r1i1p1')

    assert context.hit_count > 1

    context = conn.new_context(
        query='cmip5.output1.NIMR-KMA.HadGEM2-AO.rcp60.mon.atmos.Amon.r1i1p1',
        replica=False)

    assert context.hit_count == 1

def test_response_from_bad_parameter():
    # Test that a bad parameter name raises a useful exception
    # NOTE::: !!! This fails because urllib2 HTTP query is overrided with 
    #         !!! cache handler instead of usual response. 
    #         !!! Fix needs to make sure cached URL request has response exceptions matching urllib2 exception
    conn = SearchConnection(TEST_SERVICE)
    context = conn.new_context(project='CMIP5', rubbish='nonsense')
    context.hit_count

    try:
        context.hit_count
    except Exception, err:
        assert str(err).strip() == "Invalid query parameter(s): rubbish"
        

