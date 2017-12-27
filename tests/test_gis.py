import oasis.gis
import unittest


class TestGis(unittest.TestCase):

    def test_distance_miles(self):
        self.assertAlmostEqual(
            oasis.gis.distance_lat_lng(41.881832, -87.623177, 40.712772, -74.006058, 'm'),
            710.661184655,
            4)

    def test_distance_nautical(self):
        self.assertAlmostEqual(
            oasis.gis.distance_lat_lng(41.881832, -87.623177, 40.712772, -74.006058, 'n'),
            617.1381727544165,
            4)

    def test_distance_kilometers(self):
        self.assertAlmostEqual(
            oasis.gis.distance_lat_lng(41.881832, -87.623177, 40.712772, -74.006058, 'k'),
            1143.6983135574433,
            4)
