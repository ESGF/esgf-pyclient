
from pyesgf.search import SearchConnection

def test_pcmdi():
    # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
    conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search',distrib=True)

    ctx = conn.new_context(experiment='piControl', time_frequency='day', variable='pr', ensemble='r1i1p1')
    ctx = ctx.constrain(query='cmip5.output1.BCC.bcc-csm1-1-m.piControl.day.atmos.day.r1i1p1')
    s = ctx.search()

    ds = s[0]

    publicationDataset, server = ds.dataset_id.split('|')
    print publicationDataset, server, ds.json['replica']
    
    searchContext = ds.file_context()
    searchContext=searchContext.constrain(variable='pr')
    for j in searchContext.search():
        print j.download_url, j.checksum, j.checksum_type, j.size
