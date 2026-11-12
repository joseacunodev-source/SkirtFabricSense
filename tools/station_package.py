"""Build, verify or launch a portable research station; never install packages."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

if __package__:
    from .verify_release import digest, entries, json_object, no_links, relative_path, verify as verify_app
else:
    from verify_release import digest, entries, json_object, no_links, relative_path, verify as verify_app

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROLES = ('localizer', 'presence', 'fabric')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def model_files(directory):
    directory = Path(directory).absolute()
    for name in ('model.tflite', 'run.json'):
        no_links(directory / name)
    record = json_object(directory / 'run.json')
    require(record.get('status') == 'completed', 'Model run must be complete')
    require(record.get('export', {}).get('sha256') == digest(directory / 'model.tflite'),
            'Model hash differs from completed run')
    return record, [directory / 'model.tflite', directory / 'run.json']


def verify_station(package):
    package = Path(package).absolute()
    no_links(package)
    no_links(package / 'station-inventory.json')
    no_links(package / 'station.json')
    inventory = json_object(package / 'station-inventory.json')
    config = json_object(package / 'station.json')
    for record in (inventory, config):
        require(record.get('schema_version') == 1 and type(record['schema_version']) is int
                and record.get('status') == 'research_only' and record.get('pi_verified') is False,
                'Unsupported research station metadata')
    require(config.get('application') == 'application' and config.get('calibrated_length') is False,
            'Unsupported application or length declaration')
    require(inventory.get('dependencies_included') is False, 'Dependency payload is unsupported')
    payload = entries(inventory.get('files'), sizes=True)
    actual, directories = set(), set()
    for current, dirs, files in os.walk(package, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            no_links(path)
            name = relative_path(path.relative_to(package).as_posix())
            if path.is_dir():
                directories.add(name)
            elif path.is_file():
                actual.add(name)
            else:
                raise ValueError('Nonregular station payload')
    require(actual == set(payload) | {'station-inventory.json'}, 'Station inventory membership mismatch')
    expected_dirs = {p.as_posix() for name in payload for p in Path(name).parents if str(p) != '.'}
    require(directories == expected_dirs, 'Unexpected station directories')
    for name, record in payload.items():
        path = package / name
        require(path.stat().st_size == record['bytes'] and digest(path) == record['sha256'],
                'Station payload changed: ' + name)
    require(set(config.get('models', {})) == set(MODEL_ROLES), 'Required research model roles missing')
    for role in MODEL_ROLES:
        identity = config['models'][role]
        require(identity.get('directory') == 'models/' + role, 'Unsupported model directory')
        record, _ = model_files(package / identity['directory'])
        require(record['export']['sha256'] == identity.get('sha256'), 'Configured model identity differs')
    app_result = verify_app(package / 'application', require_app=True)
    return {'status':'passed', 'payload_files':len(payload), 'application':app_result,
            'models':config['models'], 'pi_verified':False, 'dependencies_included':False,
            'runtime_verified':False, 'calibrated_length':False}


def build(root, output, presence, application=None):
    root, output = Path(root).absolute(), Path(output).absolute()
    no_links(root)
    require(not output.exists(), 'Refusing to overwrite station package')
    for path in (output, *output.parents):
        if path.exists():
            no_links(path)
    bundle = (root / 'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
              if application is None else Path(application))
    if not bundle.is_absolute():
        bundle = root / bundle
    verify_app(bundle, require_app=True)
    sources = {p.relative_to(bundle).as_posix():p for p in bundle.rglob('*') if p.is_file()}
    model_sources = {'localizer':root/'artifacts/models/skirt-localizer-v2',
                     'presence':Path(presence).absolute(), 'fabric':root/'artifacts/models/fabric-smoke-v1'}
    require(all(not output.resolve().is_relative_to(source.resolve())
                for source in (bundle,*model_sources.values())),
            'Output must not be inside an immutable input bundle or model directory')
    config = {'schema_version':1, 'status':'research_only', 'pi_verified':False,
              'application':'application', 'calibrated_length':False, 'models':{},
              'fabric_requires_launch_opt_in':True,
              'limits':['Source-domain development only; not demonstration acceptance',
                        'Fabric is an unapproved source-appearance smoke model',
                        'No calibrated length, dependency installer or Pi verification']}
    payload = [('application/'+name, path) for name, path in sources.items()]
    for role, directory in model_sources.items():
        record, files = model_files(directory)
        config['models'][role] = {'directory':'models/'+role, 'sha256':record['export']['sha256']}
        payload.extend(('models/'+role+'/'+p.name,p) for p in files)
    payload.extend([('station_package.py',Path(__file__)),
                    ('verify_release.py',Path(__file__).with_name('verify_release.py'))])
    output.mkdir(parents=True, exist_ok=False)
    for name, source in payload:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as incoming, target.open('xb') as outgoing:
            shutil.copyfileobj(incoming,outgoing)
        require(digest(source) == digest(target), 'Station copy changed')
    with (output/'station.json').open('x',encoding='utf-8') as stream:
        json.dump(config,stream,indent=2); stream.write('\n')
    files = [p for p in output.rglob('*') if p.is_file()]
    inventory = {'schema_version':1,'status':'research_only','pi_verified':False,
                 'dependencies_included':False,'builder_sha256':digest(Path(__file__)),
                 'files':[{'path':p.relative_to(output).as_posix(),'sha256':digest(p),
                           'bytes':p.stat().st_size} for p in sorted(files)]}
    with (output/'station-inventory.json').open('x',encoding='utf-8') as stream:
        json.dump(inventory,stream,indent=2); stream.write('\n')
    return verify_station(output)


def launch_command(package, port=8766, fabric_research=False):
    require(type(port) is int and 1 <= port <= 65535, 'Port must be1..65535')
    package = Path(package).absolute()
    verify_station(package)
    args = [sys.executable,'-B','-m','app.server','--bundle',str(package/'application'),
            '--root',str(package/'application'),'--port',str(port),'--no-review',
            '--experimental-localizer',str(package/'models/localizer'),
            '--experimental-presence',str(package/'models/presence')]
    if fabric_research:
        args += ['--experimental-fabric',str(package/'models/fabric')]
    return args


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action',required=True)
    b = sub.add_parser('build')
    b.add_argument('--root',type=Path,default=ROOT)
    b.add_argument('--output',type=Path,required=True)
    b.add_argument('--presence',type=Path,required=True)
    b.add_argument('--application',type=Path,
                   help='Verified application bundle; defaults to preserved research-v7')
    v = sub.add_parser('verify'); v.add_argument('package',type=Path)
    l = sub.add_parser('launch'); l.add_argument('package',type=Path)
    l.add_argument('--port',type=int,default=8766)
    l.add_argument('--fabric-research',action='store_true')
    l.add_argument('--check-only',action='store_true',help='Verify and print launch command; do not start a server')
    a = p.parse_args()
    if a.action == 'build':
        result = build(a.root,a.output,a.presence,a.application)
    elif a.action == 'verify':
        result = verify_station(a.package)
    else:
        command = launch_command(a.package,a.port,a.fabric_research)
        if not a.check_only:
            print('Research station; fabric appearance unapproved; calibrated length unavailable.',flush=True)
            try:
                return subprocess.call(command,cwd=a.package.absolute()/'application',
                    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            except KeyboardInterrupt:
                return 130
        result = {'status':'verified_not_started','command':command,'pi_verified':False}
    print(json.dumps(result,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
