"""
Test regular expression for matching shard end points.
"""

from pyesgf.search.consts import SHARD_REXP
import re

tests = [
"https://esgf-test.a.b.c/solr",
"http://esgf.a.c/solr/data",
"http://esgs.a.d:80/data/solr",
"esgf.a.c:80/solr",
"esgf.a.c/solr"
]

expected = [
("https://", "esgf-test.a.b.c", None, "solr"),
("http://", "esgf.a.c", None, "solr/data"),
("http://", "esgs.a.d", "80", "data/solr"),
(None, "esgf.a.c", "80", "solr"),
(None, "esgf.a.c", None, "solr")
]

keys = ("prefix", "host", "port", "suffix") 

R = re.compile("^(?P<prefix>https?://)?(?P<host>.+?):?(?P<port>\d+)?/(?P<suffix>.+)$")

def test_regex():
    for i, test in enumerate(tests):
    
        match = R.match(test)
        d = match.groupdict()
        values = tuple([d[key] for key in keys])

        assert values == expected[i]


if __name__ == "__main__":
    test_regex()

