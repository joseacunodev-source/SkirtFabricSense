import unittest
import math
from tools.training.train_localizer import scene_weights, balanced_pixel_loss

class SceneBalanceTests(unittest.TestCase):
 def test_equal_total_contribution_from_training_counts(self):
  weights=scene_weights(292,56)
  self.assertAlmostEqual(weights['positive']*292,174)
  self.assertAlmostEqual(weights['negative']*56,174)
 def test_requires_both_classes(self):
  for counts in [(0,3),(3,0),(-1,3)]:
   with self.assertRaises(ValueError):scene_weights(*counts)
 def test_spatial_reduction_before_scene_weight(self):
  try:import tensorflow as tf
  except ImportError:self.skipTest('TensorFlow checked in training environment')
  actual=tf.constant([[[[1.],[0.]]],[[[0.],[0.]]]])
  predicted=tf.constant([[[[.8],[.1]]],[[[.4],[.4]]]])
  weights=scene_weights(292,56)
  result=float(balanced_pixel_loss(actual,predicted,weights,tf).numpy())
  positive=(-5*math.log(.8)-math.log(.9))/2
  negative=-math.log(.6)
  expected=(positive*weights['positive']+negative*weights['negative'])/2
  self.assertAlmostEqual(result,expected,places=5)
  # Scalar batch loss multiplied by mean sample weight is a different objective.
  wrong=(positive+negative)/2*sum(weights.values())/2
  self.assertGreater(abs(result-wrong),.01)

if __name__=='__main__':unittest.main()
