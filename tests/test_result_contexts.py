"""Offline tests for file and aggregation contexts from dataset results."""

from unittest.mock import Mock

import pytest

from pyesgf.search.connection import SearchConnection
from pyesgf.search.context import AggregationSearchContext, FileSearchContext
from pyesgf.search.results import DatasetResult


@pytest.mark.parametrize('distrib,index_node,shards', [
    (False, 'index.example.org', None),
    (True, 'index.example.org', ['index.example.org']),
    (True, 'other.example.org', None),
    (True, None, None),
])
@pytest.mark.parametrize('context_method,context_type', [
    ('file_context', FileSearchContext),
    ('aggregation_context', AggregationSearchContext),
])
@pytest.mark.parametrize('kwargs,facets', [
    ({}, None),
    ({'facets': None}, None),
    ({'facets': 'project'}, 'project'),
    ({'facets': 'project,index_node'}, 'project,index_node'),
    ({'facets': '*'}, '*'),
])
def test_child_context_facets(distrib, index_node, shards, context_method,
                              context_type, kwargs, facets, monkeypatch,
                              capsys):
    monkeypatch.delenv('ESGF_PYCLIENT_NO_FACETS_STAR_WARNING', raising=False)
    connection = SearchConnection('https://example.org/esg-search',
                                  distrib=distrib)
    connection.get_shard_list = Mock(return_value={
        'index.example.org': [('8983', 'solr/datasets')],
    })
    connection.send_search = Mock(return_value={
        'facet_counts': {'facet_fields': {}},
        'response': {'numFound': 0, 'docs': []},
    })
    parent_context = connection.new_context(facets='source_id')
    dataset_id = 'example.dataset|data.example.org'
    record = {'id': dataset_id}
    if index_node is not None:
        record['index_node'] = index_node
    result = DatasetResult(record, parent_context)

    child_context = getattr(result, context_method)(**kwargs)

    assert isinstance(child_context, context_type)
    assert child_context.connection is connection
    assert child_context.facets == facets
    assert child_context.shards == shards
    assert child_context.facet_constraints['dataset_id'] == dataset_id
    assert parent_context.facets == 'source_id'
    connection.send_search.assert_not_called()
    if distrib:
        connection.get_shard_list.assert_called_once_with()
    else:
        connection.get_shard_list.assert_not_called()

    child_context.search()

    counts_call, results_call = connection.send_search.call_args_list
    assert counts_call.args[0]['facets'] == (facets or '*')
    assert counts_call.args[0]['type'] == child_context.search_type
    assert counts_call.kwargs['limit'] == 0
    assert results_call.args[0]['facets'] == facets
    assert results_call.args[0]['type'] == child_context.search_type
    assert results_call.kwargs['shards'] == shards
    stderr = capsys.readouterr().err
    assert ('Warning - defaulting to search with facets=*' in stderr) == (
        distrib and facets is None)
