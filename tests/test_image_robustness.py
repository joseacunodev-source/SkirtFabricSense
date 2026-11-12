import unittest
from PIL import Image
from tools.evaluate_image_robustness import transform,counts,paired

class RobustnessTests(unittest.TestCase):
 def test_transform_pixels_and_sizes(self):
  image=Image.new('RGB',(3,3),(100,120,140))
  self.assertEqual(transform(image,'brightness_0.8').getpixel((1,1)),(80,96,112))
  self.assertEqual(transform(image,'gaussian_blur_radius_1').size,(3,3))
  with self.assertRaises(ValueError):transform(image,'unknown')
 def test_denominators_include_unavailable(self):
  rows=[{'sample_id':'a','target':1,'truth':'pleated','accepted':False,'prediction':None},{'sample_id':'b','target':0,'truth':None,'accepted':False,'prediction':None}]
  self.assertEqual(counts(rows),{'positive_total':1,'positive_accepted':0,'correct_pleating':0,'negative_total':1,'negative_rejected':1})
 def test_pairs_reject_changed_membership_and_truth(self):
  a=[{'sample_id':'a','target':1,'truth':'pleated','accepted':True,'prediction':'pleated'}]
  b=[{**a[0],'accepted':False,'prediction':None}]
  self.assertEqual(paired(a,b),{'correct -> unavailable':1})
  with self.assertRaises(ValueError):paired(a,[{**b[0],'sample_id':'b'}])
  with self.assertRaises(ValueError):paired(a,[{**b[0],'truth':'non_pleated'}])
if __name__=='__main__':unittest.main()
