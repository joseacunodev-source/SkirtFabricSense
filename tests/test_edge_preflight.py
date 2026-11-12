import unittest
from tools.edge_preflight import assess


class EdgePreflightTests(unittest.TestCase):
    def fixture(self):
        return {'system':'Linux', 'machine':'aarch64', 'pointer_bits':64,
                'board_model':'Raspberry Pi 5 Model B',
                'packages':{'numpy':'synthetic', 'Pillow':'synthetic', 'ai-edge-litert':'synthetic'}}

    def test_synthetic_platform_match_does_not_verify_deployment(self):
        result = assess(self.fixture())
        self.assertTrue(result['platform_and_distribution_checks_passed'])
        self.assertFalse(result['pi_verified'])
        self.assertTrue(result['remaining_checks'])

    def test_desktop_cannot_pass_as_pi(self):
        for key, value in [('system','Windows'), ('machine','x86_64'), ('pointer_bits',32), ('board_model','')]:
            with self.subTest(key=key):
                observation = dict(self.fixture(), **{key:value})
                self.assertFalse(assess(observation)['platform_and_distribution_checks_passed'])

    def test_missing_distributions_are_reported(self):
        observation = self.fixture()
        observation['packages'] = {}
        result = assess(observation)
        self.assertEqual(len(result['blockers']), 3)
        self.assertEqual(result['runtime_distributions'], [])


if __name__ == '__main__':
    unittest.main()
