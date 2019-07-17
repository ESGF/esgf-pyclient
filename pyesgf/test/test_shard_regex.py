"""
Test regular expression for matching shard end points.
"""

import re
from unittest import TestCase

R = re.compile(r"^(?P<prefix>https?://)?(?P<host>.+?)"
               r":?(?P<port>\d+)?/(?P<suffix>.+)$")


class TestShardRegex(TestCase):
    def setUp(self):
        self.keys = ("prefix", "host", "port", "suffix")
        self.tests = ["https://esgf-test.a.b.c/solr",
                      "http://esgf.a.c/solr/data",
                      "http://esgs.a.d:80/data/solr",
                      "esgf.a.c:80/solr",
                      "esgf.a.c/solr"]
        self.expected = [("https://", "esgf-test.a.b.c", None, "solr"),
                         ("http://", "esgf.a.c", None, "solr/data"),
                         ("http://", "esgs.a.d", "80", "data/solr"),
                         (None, "esgf.a.c", "80", "solr"),
                         (None, "esgf.a.c", None, "solr")]

    def test_regex(self):
        for i, test in enumerate(self.tests):

            match = R.match(test)
            d = match.groupdict()
            values = tuple([d[key] for key in self.keys])

            assert values == self.expected[i]
