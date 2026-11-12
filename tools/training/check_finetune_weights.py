"""Verify frozen backbone and BatchNorm weights stayed unchanged in a pilot."""
import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--parent',type=Path,required=True)
p.add_argument('--child',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():raise ValueError('Output exists')
old=tf.keras.models.load_model(a.parent,compile=False)
new=tf.keras.models.load_model(a.child,compile=False)
before=next(l for l in old.layers if isinstance(l,tf.keras.Model))
after=next(l for l in new.layers if isinstance(l,tf.keras.Model))
frozen_changes=[];tuned_changes=[]
for i,(left,right) in enumerate(zip(before.layers,after.layers)):
    assert left.name==right.name
    changed=any(not np.array_equal(x,y) for x,y in zip(left.get_weights(),right.get_weights()))
    frozen=i<len(before.layers)-30 or isinstance(left,tf.keras.layers.BatchNormalization)
    if changed:(frozen_changes if frozen else tuned_changes).append(left.name)
head_changed=any(not np.array_equal(x,y) for x,y in zip(old.layers[-1].get_weights(),new.layers[-1].get_weights()))
report=dict(status='passed' if not frozen_changes and tuned_changes and head_changed else 'failed',
            frozen_layer_changes=frozen_changes,tuned_layer_changes=tuned_changes,head_changed=head_changed)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['status']=='passed' else 1)
