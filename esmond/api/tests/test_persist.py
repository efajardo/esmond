"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import os.path
import json
import datetime
import calendar
import shutil
import time

from collections import namedtuple

from django.test import TestCase
from django.conf import settings

from esmond.api.models import Device, IfRef, ALUSAPRef

from esmond.persist import IfRefPollPersister, ALUSAPRefPersister, \
     PersistQueueEmpty, TSDBPollPersister, CassandraPollPersister
from esmond.config import get_config, get_config_path
from esmond.cassandra import CASSANDRA_DB
from pycassa.columnfamily import ColumnFamily

try:
    import tsdb
    from tsdb.row import ROW_VALID
except ImportError:
    tsdb = None


def load_test_data(name):
    path = os.path.join(settings.ESMOND_ROOT, "..", "test_data", name)
    d = json.loads(open(path).read())
    return d

ifref_test_data = """
[{
    "oidset_name": "IfRefPoll",
    "device_name": "router_a",
    "timestamp": 1345125600,
    "oid_name": "",
    "data": {
        "ifSpeed": [ [ "ifSpeed.1", 1000000000 ] ],
        "ifType": [ [ "ifType.1", 53 ] ],
        "ipAdEntIfIndex": [ [ "ipAdEntIfIndex.10.37.37.1", 1 ] ],
        "ifHighSpeed": [ [ "ifHighSpeed.1", 1000 ] ],
        "ifAlias": [ [ "ifAlias.1", "test one" ] ],
        "ifPhysAddress": [ [ "ifPhysAddress.1", "\u0000\u001c\u000fFk@" ] ],
        "ifAdminStatus": [ [ "ifAdminStatus.1", 1 ] ],
        "ifDescr": [ [ "ifDescr.1", "Vlan1" ] ],
        "ifMtu": [ [ "ifMtu.1", 1500 ] ],
        "ifOperStatus": [ [ "ifOperStatus.1", 1 ] ]
    }
},
{
    "oidset_name": "IfRefPoll",
    "device_name": "router_a",
    "timestamp": 1345125660,
    "oid_name": "",
    "data": {
        "ifSpeed": [ [ "ifSpeed.1", 1000000000 ] ],
        "ifType": [ [ "ifType.1", 53 ] ],
        "ipAdEntIfIndex": [ [ "ipAdEntIfIndex.10.37.37.1", 1 ] ],
        "ifHighSpeed": [ [ "ifHighSpeed.1", 1000 ] ],
        "ifAlias": [ [ "ifAlias.1", "test two" ] ],
        "ifPhysAddress": [ [ "ifPhysAddress.1", "\u0000\u001c\u000fFk@" ] ],
        "ifAdminStatus": [ [ "ifAdminStatus.1", 1 ] ],
        "ifDescr": [ [ "ifDescr.1", "Vlan1" ] ],
        "ifMtu": [ [ "ifMtu.1", 1500 ] ],
        "ifOperStatus": [ [ "ifOperStatus.1", 1 ] ]
    }
}]
"""

empty_ifref_test_data = """
[{
    "oidset_name": "IfRefPoll",
    "device_name": "router_a",
    "timestamp": 1345125720,
    "oid_name": "",
    "data": {
        "ifSpeed": [],
        "ifType": [],
        "ipAdEntIfIndex": [],
        "ifHighSpeed": [],
        "ifAlias": [],
        "ifPhysAddress": [],
        "ifAdminStatus": [],
        "ifDescr": [],
        "ifMtu": [],
        "ifOperStatus": []
    }
}]"""

class TestPollResult(object):
    def __init__(self, d):
        self.__dict__.update(d)

    def __repr__(self):
        s = "TestPollResult("
        for k,v in self.__dict__.iteritems():
            s += "%s: %s, " % (k,v)
        s = s[:-2] + ")"

        return s

class TestPersistQueue(object):
    """Data is a list of dicts, representing the objects"""
    def __init__(self, data):
        self.data = data

    def get(self):
        try:
            return TestPollResult(self.data.pop(0))
        except IndexError:
            raise PersistQueueEmpty()

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class TestIfRefPersister(TestCase):
    fixtures = ['test_devices.json']

    def test_test(self):
        d = Device.objects.get(name="router_a")
        self.assertEqual(d.name, "router_a")

    def test_persister(self):
        ifrefs = IfRef.objects.filter(device__name="router_a", ifDescr="Vlan1")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 0)

        q = TestPersistQueue(json.loads(ifref_test_data))
        p = IfRefPollPersister([], "test", persistq=q)
        p.run()

        ifrefs = IfRef.objects.filter(device__name="router_a", ifDescr="Vlan1")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 2)

        self.assertEqual(ifrefs[0].ifIndex, ifrefs[1].ifIndex)
        self.assertTrue(ifrefs[0].end_time < datetime.datetime.max)
        self.assertTrue(ifrefs[1].end_time == datetime.datetime.max)
        self.assertTrue(ifrefs[0].ifAlias == "test one")
        self.assertTrue(ifrefs[1].ifAlias == "test two")

        q = TestPersistQueue(json.loads(empty_ifref_test_data))
        p = IfRefPollPersister([], "test", persistq=q)
        p.run()

        ifrefs = IfRef.objects.filter(device__name="router_a", ifDescr="Vlan1")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 2)

        self.assertTrue(ifrefs[1].end_time < datetime.datetime.max)

alu_sap_test_data = """
[
    {
        "oidset_name": "ALUSAPRefPoll",
        "device_name": "router_a",
        "timestamp": 1345125600,
        "oid_name": "",
        "data": {
            "sapDescription": [
                [ "sapDescription.1.1342177281.100", "one" ]
            ],
            "sapIngressQosPolicyId": [
                [ "sapIngressQosPolicyId.1.1342177281.100", 2 ]
            ],
            "sapEgressQosPolicyId": [
                [ "sapEgressQosPolicyId.1.1342177281.100", 2 ]
            ]
        },
        "metadata": {}
    },
    {
        "oidset_name": "ALUSAPRefPoll",
        "device_name": "router_a",
        "timestamp": 1345125660,
        "oid_name": "",
        "data": {
            "sapDescription": [
                [ "sapDescription.1.1342177281.100", "two" ]
            ],
            "sapIngressQosPolicyId": [
                [ "sapIngressQosPolicyId.1.1342177281.100", 2 ]
            ],
            "sapEgressQosPolicyId": [
                [ "sapEgressQosPolicyId.1.1342177281.100", 2 ]
            ]
        },
        "metadata": {}
    }
]
"""
empty_alu_sap_test_data = """
[
    {
        "oidset_name": "ALUSAPRefPoll",
        "device_name": "router_a",
        "timestamp": 1345125720,
        "oid_name": "",
        "data": {
            "sapDescription": [],
            "sapIngressQosPolicyId": [],
            "sapEgressQosPolicyId": []
        },
        "metadata": {}
    }
]"""
class TestALUSAPRefPersister(TestCase):
    fixtures = ['test_devices.json']

    def test_persister(self):
        ifrefs = IfRef.objects.filter(device__name="router_a")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 0)

        q = TestPersistQueue(json.loads(alu_sap_test_data))
        p = ALUSAPRefPersister([], "test", persistq=q)
        p.run()

        ifrefs = ALUSAPRef.objects.filter(device__name="router_a", name="1-8_0_0-100")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 2)

        self.assertTrue(ifrefs[0].end_time < datetime.datetime.max)
        self.assertTrue(ifrefs[1].end_time == datetime.datetime.max)
        self.assertTrue(ifrefs[0].sapDescription == "one")
        self.assertTrue(ifrefs[1].sapDescription == "two")

        q = TestPersistQueue(json.loads(empty_alu_sap_test_data))
        p = ALUSAPRefPersister([], "test", persistq=q)
        p.run()

        ifrefs = ALUSAPRef.objects.filter(device__name="router_a", name="1-8_0_0-100")
        ifrefs = ifrefs.order_by("end_time").all()
        self.assertTrue(len(ifrefs) == 2)

        self.assertTrue(ifrefs[1].end_time < datetime.datetime.max)

# XXX(jdugan): it would probably be better and easier in the long run to keep
# these JSON blobs in files and define a small class to load them
timeseries_test_data = """
[
    {
        "oidset_name": "FastPollHC",
        "device_name": "router_a",
        "timestamp": 1343953700,
        "oid_name": "ifHCInOctets",
        "data": [
            [
                "ifHCInOctets/GigabitEthernet0_1",
                25066556556930
            ],
            [
                "ifHCInOctets/GigabitEthernet0_2",
                126782001836
            ],
            [
                "ifHCInOctets/GigabitEthernet0_3",
                27871397880
            ],
            [
                "ifHCInOctets/Loopback0",
                0
            ]
        ],
        "metadata": {
            "tsdb_flags": 1
        }
    },
    {
        "oidset_name": "FastPollHC",
        "device_name": "router_a",
        "timestamp": 1343953730,
        "oid_name": "ifHCInOctets",
        "data": [
            [
                "ifHCInOctets/GigabitEthernet0_1",
                25066575790604
            ],
            [
                "ifHCInOctets/GigabitEthernet0_2",
                126782005062
            ],
            [
                "ifHCInOctets/GigabitEthernet0_3",
                27871411592
            ],
            [
                "ifHCInOctets/Loopback0",
                0
            ]
        ],
        "metadata": {
            "tsdb_flags": 1
        }
    }
]
"""

class TestCassandraPollPersister(TestCase):
    fixtures = ['test_devices.json', 'oidsets.json']

    def setUp(self):
        """make sure we have a clean router_a directory to start with."""
        router_a_path = os.path.join(settings.ESMOND_ROOT, "tsdb-data", "router_a")
        if os.path.exists(router_a_path):
            shutil.rmtree(router_a_path, ignore_errors=True)

    def test_persister(self):
        """This is a very basic smoke test for a cassandra persister."""
        config = get_config(get_config_path())
        test_data = json.loads(timeseries_test_data)
        return
        q = TestPersistQueue(test_data)
        p = CassandraPollPersister(config, "test", persistq=q)
        p.run()
        p.db.close()
        p.db.stats.report('all')

    def test_persister_long(self):
        """Make sure the tsdb and cassandra data match"""
        config = get_config(get_config_path())
        test_data = load_test_data("router_a_ifhcin_long.json")

        config.db_clear_on_testing = True
        config.db_profile_on_testing = True

        q = TestPersistQueue(test_data)
        p = CassandraPollPersister(config, "test", persistq=q)
        p.run()
        p.db.flush()
        p.db.close()
        p.db.stats.report('all')

        test_data = load_test_data("router_a_ifhcin_long.json")
        q = TestPersistQueue(test_data)
        p = TSDBPollPersister(config, "test", persistq=q)
        p.run()

        path_levels = []

        router_a_path = os.path.join(settings.ESMOND_ROOT, "tsdb-data", "router_a")
        for (path, dirs, files) in os.walk(router_a_path):
            if dirs[0] == 'TSDBAggregates':
                break
            path_levels.append(dirs)

        oidsets = path_levels[0]
        oids    = path_levels[1]
        paths   = path_levels[2]

        full_paths = {}

        for oidset in oidsets:
            for oid in oids:
                for path in paths:
                    full_path = 'router_a/%s/%s/%s/TSDBAggregates/30'  % \
                        (oidset, oid, path)
                    if not full_paths.has_key(full_path):
                        full_paths[full_path] = 1

        ts_db = tsdb.TSDB(config.tsdb_root)
        db = CASSANDRA_DB(config)

        rates = ColumnFamily(db.pool, db.rate_cf)

        count_bad = 0
        tsdb_aggs = 0

        for p in full_paths.keys():
            v = ts_db.get_var(p)
            device,oidset,oid,path,tmp1,tmp2 = p.split('/')
            for d in v.select():
                tsdb_aggs += 1
                key = '%s:%s:%s:%s:%s:%s'  % \
                    (device,oidset,oid,path,int(tmp2)*1000,
                    datetime.datetime.utcfromtimestamp(d.timestamp).year)

                val = rates.get(key, [d.timestamp*1000])[d.timestamp*1000]
                print val
                if d.flags != ROW_VALID:
                    assert val['is_valid'] == 0
                else:
                    assert val['val'] == d.delta
                    assert val['is_valid'] > 0

        db.close()

    def test_range_baserate_query(self):
        """
        Presumed using test data loaded in previous test method.

        Shows the three query methods that return json formatted data.

        All args shown other than as_json are required.
        """
        config = get_config(get_config_path())
        db = CASSANDRA_DB(config)
        return
        start_time = 1343956800
        end_time = 1343957400
        expected_results = 21

        ret = db.query_baserate_timerange(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            freq=30,
            ts_min=start_time,
            ts_max=end_time
        )

        assert len(ret) == expected_results

        ret = db.query_baserate_timerange(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            freq=30,
            ts_min=start_time,
            ts_max=end_time,
            cf='average', # average | delta - optional
            as_json=True
        )

        ret = json.loads(ret)

        assert len(ret['data']) == expected_results
        assert ret['begin_time'] == start_time
        assert ret['end_time'] == end_time

        ret = db.query_raw_data(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            freq=30,
            ts_min=start_time,
            ts_max=end_time,
            as_json=True
        )

        ret = json.loads(ret)

        assert len(ret['data']) == expected_results - 1

        ret = db.query_aggregation_timerange(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            ts_min=start_time - 3600,
            ts_max=end_time,
            freq=3600, # required!
            cf='average',  # min | max | average - also required!
            as_json=True
        )

        ret = json.loads(ret)

        assert ret['agg'] == 3600
        assert ret['data'][0][1] == 17

        ret = db.query_aggregation_timerange(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            ts_min=start_time - 3600,
            ts_max=end_time,
            freq=3600, # required!
            cf='min',  # min | max | average - also required!
            as_json=True
        )

        ret = json.loads(ret)

        assert ret['agg'] == 3600
        assert ret['data'][0][1] == 0

        ret = db.query_aggregation_timerange(
            device='router_a',
            path='fxp0.0',
            oid='ifHCInOctets',
            ts_min=start_time - 3600,
            ts_max=end_time,
            freq=3600, # required!
            cf='max',  # min | max | average - also required!
            as_json=True
        )

        ret = json.loads(ret)

        assert ret['agg'] == 3600
        assert ret['data'][0][1] == 7500

        db.close()


if tsdb:
    class TestTSDBPollPersister(TestCase):
        fixtures = ['test_devices.json', 'oidsets.json']

        def setUp(self):
            """make sure we have a clean router_a directory to start with."""
            router_a_path = os.path.join(settings.ESMOND_ROOT, "tsdb-data", "router_a")
            if os.path.exists(router_a_path):
                shutil.rmtree(router_a_path)


        def test_persister(self):
            """This is a very basic smoke test for a TSDB persister."""
            config = get_config(get_config_path())

            test_data = json.loads(timeseries_test_data)
            q = TestPersistQueue(test_data)
            p = TSDBPollPersister(config, "test", persistq=q)
            p.run()

            test_data = json.loads(timeseries_test_data)
            db = tsdb.TSDB(config.tsdb_root)
            for pr in test_data:
                for oid, val in pr['data']:
                    iface = oid.split('/')[-1]
                    path = "%s/%s/%s/%s/" % (pr['device_name'],
                            pr['oidset_name'], pr['oid_name'], iface)
                    v = db.get_var(path)
                    d = v.get(pr['timestamp'])
                    self.assertEqual(val, d.value)

        def test_persister_long(self):
            """Use actual data to test persister"""
            config = get_config(get_config_path())

            # load example data

            test_data = load_test_data("router_a_ifhcin_long.json")
            q = TestPersistQueue(test_data)
            p = TSDBPollPersister(config, "test", persistq=q)
            p.run()
            sys.exit()

            test_data = load_test_data("router_a_ifhcin_long.json")
            ts0 = test_data[0]['timestamp']
            tsn = test_data[-1]['timestamp']

            # make sure it got written to disk as expected

            db = tsdb.TSDB(config.tsdb_root)
            paths = []
            for pr in test_data:
                for oid, val in pr['data']:
                    iface = oid.split('/')[-1]
                    path = "%s/%s/%s/%s/" % (pr['device_name'],
                            pr['oidset_name'], pr['oid_name'], iface)
                    if path not in paths:
                        paths.append(path)
                    v = db.get_var(path)
                    d = v.get(pr['timestamp'])
                    self.assertEqual(val, d.value)

            # check that aggregates were calculated as expected

            db = tsdb.TSDB(config.tsdb_root)
            aggs = load_test_data("router_a_ifhcin_long_agg.json")
            for path in paths:
                p = path + "TSDBAggregates/30"
                v = db.get_var(p)
                for d in v.select(begin=ts0, end=tsn):
                    average, delta = aggs[p][str(d.timestamp)]
                    self.assertEqual(d.average, average)
                    self.assertEqual(d.delta, delta)
                v.close()