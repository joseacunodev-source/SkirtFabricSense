"""Run deterministic synthetic controller scenarios without opening a camera."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.live_state import Frame, LiveController


def replay():
    now = [0.0]
    controller = LiveController(max_frame_age=1.0, max_result_age=2.0, clock=lambda:now[0])
    trace = []
    def record(event):
        trace.append({'event':event,'simulation_time':now[0],**controller.snapshot()})
    def frame(n):
        return Frame(n,now[0],{'synthetic_frame':n})
    placeholder = {'style':{'status':'synthetic_test_value'},
                   'fabric':{'status':'unavailable'},'length':{'status':'unavailable'}}
    controller.set_connected(True)
    controller.submit(frame(1),valid=True)
    first=controller.take()
    now[0]=0.1
    controller.submit(frame(2),valid=True)
    now[0]=0.2
    controller.submit(frame(3),valid=True)
    assert controller.take() is None
    assert controller.snapshot()['pending_frame_id']==3
    record('newest_waiting_frame_replaces_older')
    controller.invalidate('scene_changed')
    controller.submit(frame(4),valid=True)
    assert controller.finish(first,placeholder) is False
    record('old_scene_completion_rejected')
    current=controller.take()
    assert current.frame.frame_id==4
    assert controller.finish(current,placeholder)
    record('current_scene_result_accepted')
    now[0]=2.21
    assert controller.snapshot()['result'] is None
    record('capture_age_expired')
    controller.submit(frame(5),valid=True)
    active=controller.take()
    controller.set_connected(False)
    controller.set_connected(True)
    controller.submit(frame(6),valid=True)
    assert controller.finish(active,placeholder) is False
    record('pre_disconnect_completion_rejected')
    active=controller.take()
    assert controller.finish(active,placeholder)
    controller.submit(frame(7),valid=False)
    assert controller.snapshot()['result'] is None
    record('invalid_frame_clears_result')
    controller.submit(frame(8),valid=True)
    active=controller.take()
    assert controller.finish(active,error='synthetic worker failure') is False
    record('inference_error_clears_result')
    return trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    trace=replay()
    paths=['app/live_state.py','tools/replay_live_state.py']
    evidence={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
              'status':'passed','kind':'synthetic_controller_replay',
              'configuration':{'max_frame_age_seconds':1.0,'max_result_age_seconds':2.0,
                               'status':'test_configuration_not_calibrated_product_thresholds'},
              'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
              'trace':trace,'camera_opened':False,'model_executed':False,'pi_verified':False,
              'limitations':'Synthetic events and clock; no camera detection, measured speed, accuracy or hardware reliability evidence.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(evidence,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'status':'passed','scenario_checkpoints':len(trace),'camera_opened':False}))


if __name__=='__main__':
    main()
