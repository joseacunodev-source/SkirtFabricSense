"""Synthetic opt-in fabric integration checks; no camera or accuracy claims."""
import unittest
from unittest.mock import Mock

from PIL import Image
from app.localization import AutomaticPredictor


class FabricIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGB', (1000,800), (80,100,120))
        self.options = dict(presentation='worn', fabric_enabled=True,
                            source_frame_id='current-frame-17', camera_config_id=None)
        self.localizer = Mock()
        self.localizer.locate.return_value = dict(status='provisional', roi=[200,300,600,700])
        self.pleating = Mock()
        self.pleating.predict.return_value = dict(style=dict(status='provisional', label='pleated'),
            metadata=dict(model_sha256='synthetic-pleating', roi_xyxy=[180,280,620,720]))
        self.fabric = Mock()
        self.fabric.predict.return_value = dict(status='research_only', label='source_denim_appearance',
            composition_verified=False, live_approved=False, pi_verified=False)

    def wrapper(self, **kwargs):
        return AutomaticPredictor(self.pleating, self.localizer, fabric=self.fabric, **kwargs)

    def test_toggle_off_does_not_invoke_fabric(self):
        result = self.wrapper().predict(self.image, {**self.options,'fabric_enabled':False})
        self.fabric.predict.assert_not_called()
        self.assertEqual(result['fabric']['status'],'disabled')
        self.assertEqual(result['style']['label'],'pleated')

    def test_current_original_source_and_localizer_roi_preserved(self):
        result = self.wrapper().predict(self.image,self.options)
        args = self.fabric.predict.call_args.args
        self.assertIs(args[0],self.image)
        self.assertEqual(args[0].size,(1000,800))
        self.assertEqual(args[1],(200,300,600,700))
        self.assertNotEqual(list(args[1]),result['metadata']['roi_xyxy'])
        self.pleating.predict.assert_called_once_with(self.image,(200,300,600,700),True)
        self.assertEqual(result['fabric']['source_frame_id'],'current-frame-17')
        self.assertEqual(result['fabric']['status'],'research_only')
        self.assertFalse(result['fabric']['composition_verified'])
        self.assertFalse(result['fabric']['live_approved'])

    def test_fabric_failure_preserves_independent_pleating(self):
        self.fabric.predict.side_effect = ValueError('unsupported ROI or invalid model output')
        result = self.wrapper().predict(self.image,self.options)
        self.assertEqual(result['fabric']['status'],'unavailable')
        self.assertEqual(result['fabric']['reason'],'experimental_fabric_provider_failed')
        self.assertEqual(result['style']['label'],'pleated')
        self.assertEqual(result['metadata']['pleating_model_sha256'],'synthetic-pleating')

    def test_unavailable_localization_prevents_fabric(self):
        for reason in ['multiple_regions','region_touches_frame_edge','no_supported_skirt_region']:
            self.localizer.locate.return_value=dict(status='unavailable',roi=None,reason=reason)
            result=self.wrapper().predict(self.image,self.options)
            self.assertEqual(result['fabric']['status'],'unavailable')
            self.assertEqual(result['style']['status'],'unavailable')
        self.fabric.predict.assert_not_called()
        self.pleating.predict.assert_not_called()

    def test_presence_rejection_prevents_fabric(self):
        presence=Mock();presence.check.return_value=dict(accepted=False)
        result=self.wrapper(presence=presence).predict(self.image,self.options)
        self.assertEqual(result['fabric']['status'],'unavailable')
        self.fabric.predict.assert_not_called()
        self.localizer.locate.assert_not_called()

    def test_default_provider_keeps_fabric_unavailable(self):
        wrapper=AutomaticPredictor(self.pleating,self.localizer)
        self.assertIsNone(wrapper.fabric)
        result=wrapper.predict(self.image,self.options)
        self.assertEqual(result['fabric']['status'],'unavailable')
        self.assertEqual(result['style']['label'],'pleated')

    def test_no_localizer_prevents_fabric(self):
        result=AutomaticPredictor(self.pleating,fabric=self.fabric).predict(self.image,self.options)
        self.assertEqual(result['fabric']['status'],'unavailable')
        self.fabric.predict.assert_not_called()


if __name__=='__main__':unittest.main()
