import unittest
from app.hemline import classify_hemline, LABELS, MODES


class HemlineTests(unittest.TestCase):
    def setUp(self):
        # Synthetic boundaries exercise code only; not production thresholds.
        self.profile={'profile_id':'synthetic','reference_id':'fixture-test',
                      'coordinate':'waist_to_floor','labels':list(LABELS),
                      'supported_modes':list(MODES),'boundaries':[.1,.2,.3,.4,.5,.6,.7,.8]}

    def classify(self, interval, **kw):
        return classify_hemline(mode=kw.get('mode','worn'),hem_interval=interval,
                                profile=self.profile,reference_id='fixture-test')

    def test_all_nine_labels(self):
        for i,label in enumerate(LABELS):
            self.assertEqual(self.classify((i/10+.04,i/10+.06))['label'],label)

    def test_no_reference_abstains_in_every_mode(self):
        for mode in MODES:
            self.assertEqual(classify_hemline(mode=mode)['reason'],'body_reference_required')

    def test_boundary_uncertainty(self):
        for interval in [(.39,.41),(.4,.4),(.1,.8)]:
            self.assertEqual(self.classify(interval)['status'],'uncertain')

    def test_unsupported_mode_for_reference(self):
        self.profile['supported_modes']=['worn']
        self.assertEqual(self.classify((.2,.25),mode='held')['status'],'unavailable')

    def test_out_of_range_and_missing_geometry(self):
        for interval in [(-.1,.1),(.9,1.1),None]:
            self.assertEqual(self.classify(interval)['status'],'unavailable')

    def test_bad_calibration_rejected(self):
        self.profile['boundaries'][1]=.1
        with self.assertRaises(ValueError):self.classify((.2,.3))

    def test_reference_mismatch_rejected(self):
        self.profile['reference_id']='another-body'
        with self.assertRaises(ValueError):self.classify((.2,.3))

    def test_invalid_interval_rejected(self):
        for interval in [(True,.3),(.4,.3),(float('nan'),.2)]:
            with self.assertRaises(ValueError):self.classify(interval)


if __name__=='__main__':unittest.main()
