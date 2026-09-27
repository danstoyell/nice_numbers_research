"""Independent oracle checks for arithmetic underlying research claims.

Run: python3 -m unittest discover -s tests
"""
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify import candidate_intervals, digits, floor_root, verify


class ExactVerificationTests(unittest.TestCase):
    def test_known_example_and_near_miss(self):
        self.assertEqual(69**2,4761)
        self.assertEqual(69**3,328509)
        self.assertEqual(sorted(str(69**2)+str(69**3)),list('0123456789'))
        self.assertTrue(verify(69,10)['nice'])
        near = verify(330169542960890,45)
        self.assertEqual(near['digit_count'],45)
        self.assertEqual(near['distinct_digits'],44)
        self.assertFalse(near['nice'])

    def test_root_inequalities(self):
        rng=random.Random(20260923)
        for exponent in range(2,8):
            for _ in range(100):
                value=rng.randrange(1,10**30)
                root=floor_root(value,exponent)
                self.assertLessEqual(root**exponent,value)
                self.assertLess(value,(root+1)**exponent)
            for root in [0,1,2,69,10**40]:
                self.assertEqual(floor_root(root**exponent,exponent),root)

    def test_all_small_inputs_match_bounds(self):
        # Independent length oracle avoids logs and verifier digit extraction.
        def length(value,base):
            size,power=1,base
            while power<=value:
                power*=base
                size+=1
            return size
        for b in range(2,19):
            intervals=candidate_intervals(b)
            upper=max([x['hi'] for x in intervals]+[1000])+20
            for n in range(1,upper+1):
                by_bounds=any(x['lo']<=n<=x['hi'] for x in intervals)
                by_powers=length(n*n,b)+length(n*n*n,b)==b
                self.assertEqual(by_bounds,by_powers,(n,b))

    def test_exact_endpoints_through_base_600(self):
        for base in range(2,601):
            for interval in candidate_intervals(base):
                lo,hi=interval['lo'],interval['hi']
                for n in [lo,hi]:
                    square,cube=digits(n*n,base),digits(n*n*n,base)
                    self.assertEqual(len(square)+len(cube),base)
                    self.assertEqual(sum(d*base**i for i,d in enumerate(reversed(square))),n*n)
                    self.assertEqual(sum(d*base**i for i,d in enumerate(reversed(cube))),n*n*n)
                if lo>1:
                    self.assertLess(verify(lo-1,base)['digit_count'],base)
                self.assertGreater(verify(hi+1,base)['digit_count'],base)


if __name__=='__main__':
    unittest.main()
