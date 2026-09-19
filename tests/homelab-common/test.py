#!/usr/bin/env python3
"""Offline Helm contract/package tests. Requires helm and PyYAML; writes only to tempdir."""
import argparse
import hashlib
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--common', action='append', type=Path, required=True,
                    help='Verified Bitnami common archive; repeat for each coexistence version')
ARGS = parser.parse_args()


def helm(*args, ok=True):
    result = subprocess.run(['helm', *map(str, args)], text=True, capture_output=True)
    if ok and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    if not ok:
        assert result.returncode, 'Expected Helm failure'
    return result.stdout + (result.stderr if not ok else '')


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='homelab-common-')
        cls.work = Path(cls.tmp.name)
        cls.library = cls.work / 'charts/homelab-common'
        shutil.copytree(ROOT / 'charts/homelab-common', cls.library)
        cls.fixture = cls.work / 'tests/homelab-common/fixture'
        shutil.copytree(ROOT / 'tests/homelab-common/fixture', cls.fixture)
        helm('dependency', 'build', cls.fixture, '--skip-refresh')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render(self, values=None, release='demo', chart=None, ok=True):
        path = self.work / 'override.yaml'
        path.write_text(yaml.safe_dump(values or {}))
        out = helm('template', release, chart or self.fixture, '-f', path, ok=ok)
        if not ok:
            return out
        return next(x for x in yaml.safe_load_all(out) if x and x['kind'] == 'ConfigMap')

    def test_defaults(self):
        obj = self.render()
        data = obj['data']
        self.assertEqual(obj['metadata']['name'], 'demo-example')
        self.assertEqual(data['name'], 'example')
        self.assertEqual(data['account'], 'default')
        self.assertEqual(data['claim'], 'demo-example-data')
        self.assertEqual(data['storage'], '')
        self.assertEqual(data['secrets'], '')
        self.assertEqual(data['image'], 'nginx:1.27')
        self.assertEqual(obj['metadata']['labels']['helm.sh/chart'], 'example-1.0.0_build')

    def test_names(self):
        for values, release, expected in [
            ({}, 'my-example', 'my-example'),
            ({'nameOverride': 'demo'}, 'demo', 'demo'),
            ({'fullnameOverride': 'fixed'}, 'demo', 'fixed'),
            ({'fullnameOverride': 'a' * 62 + '-tail'}, 'demo', 'a' * 62),
            ({'fullnameOverride': 'a' * 80}, 'demo', 'a' * 63),
            ({'nameOverride': 'alternate'}, 'demo', 'demo-alternate'),
        ]:
            with self.subTest(values=values):
                self.assertEqual(self.render(values, release)['metadata']['name'], expected)

    def test_labels(self):
        values = {'customLabels': {'app.kubernetes.io/name': 'unsafe',
                                  'app.kubernetes.io/instance': 'unsafe', 'team': 'ops'},
                  'component': 'backend'}
        obj = self.render(values)
        selector = yaml.safe_load(obj['data']['selector'])
        self.assertEqual(selector, {'app.kubernetes.io/name': 'example',
                                   'app.kubernetes.io/instance': 'demo',
                                   'app.kubernetes.io/component': 'backend'})
        self.assertTrue(all(obj['metadata']['labels'][k] == v for k, v in selector.items()))
        self.assertEqual(obj['metadata']['labels']['team'], 'ops')
        self.assertEqual(len(yaml.safe_load(self.render()['data']['selector'])), 2)

    def test_images(self):
        cases = [({'image': {'tag': ''}}, 'nginx:1.2.3'),
                 ({'image': {'registry': 'local', 'digest': 'sha256:abc'},
                   'global': {'imageRegistry': 'global'}}, 'global/nginx@sha256:abc'),
                 ({'image': {'registry': 'local'}}, 'local/nginx:1.27')]
        for values, expected in cases:
            self.assertEqual(self.render(values)['data']['image'], expected)
        self.assertIn('repository is required', self.render({'image': {'repository': ''}}, ok=False))
        values = {'global': {'imagePullSecrets': ['a', {'name': 'b'}]},
                  'imagePullSecrets': [{'name': 'a'}, 'c'], 'image': {'pullSecrets': ['b', 'd']}}
        self.assertEqual(yaml.safe_load(self.render(values)['data']['secrets']),
                         {'imagePullSecrets': [{'name': x} for x in 'abcd']})
        self.assertIn('secret name cannot be empty', self.render({'imagePullSecrets': ['']}, ok=False))
        self.assertIn('expected string', self.render({'imagePullSecrets': [3]}, ok=False))

    def test_storage_and_accounts(self):
        for persistence, global_values, expected in [({}, {}, ''),
                ({}, {'defaultStorageClass': 'global'}, 'global'),
                ({'storageClass': 'local'}, {'defaultStorageClass': 'global'}, 'local'),
                ({'storageClass': '-'}, {'defaultStorageClass': 'global'}, ''),
                ({'storageClass': ''}, {'defaultStorageClass': 'global'}, 'global'),
                ({}, {'storageClass': 'ignored'}, '')]:
            value = self.render({'persistence': persistence, 'global': global_values})['data']['storage']
            if persistence.get('storageClass') == '-':
                self.assertEqual(yaml.safe_load(value), {'storageClassName': ''})
            else:
                self.assertEqual(yaml.safe_load(value), {'storageClassName': expected} if expected else None)
        self.assertEqual(self.render({'persistence': {'existingClaim': 'keep-this'}})['data']['claim'], 'keep-this')
        for account, expected in [({}, 'default'), ({'create': True}, 'demo-example'),
                                  ({'create': False, 'name': 'existing'}, 'existing'),
                                  ({'create': True, 'name': 'custom'}, 'custom')]:
            self.assertEqual(self.render({'serviceAccount': account})['data']['account'], expected)

    def test_render_merge(self):
        data = self.render()['data']
        self.assertEqual(data['rendered'], 'demo')
        merged = yaml.safe_load(data['merged'])
        self.assertEqual(merged, {'nested': {'winner': 'first', 'retained': True},
                                 'enabled': False, 'count': 0, 'text': '', 'items': []})
        self.assertEqual(self.render({'renderValue': '{{ .key }}-{{ $.Release.Name }}',
                                     'renderScope': {'key': 'scoped'}})['data']['rendered'], 'scoped-demo')
        self.assertEqual(yaml.safe_load(self.render({'mergeValues': [{'name': '{{ .Release.Name }}'}]})['data']['merged']), {'name': 'demo'})
        self.assertIn('must be a YAML map', self.render({'mergeValues': ['- list']}, ok=False))
        self.assertEqual(yaml.safe_load(self.render({'mergeValues': []})['data']['merged']), {})

    def test_merge_argument_validation(self):
        consumer = self.work / 'merge-arguments'
        shutil.copytree(self.fixture, consumer)
        template = consumer / 'templates/configmap.yaml'
        cases = [('', 'values is required'),
                 ('"values" nil', 'values must be a list'),
                 ('"values" (dict)', 'values must be a list'),
                 ('"values" "text"', 'values must be a list'),
                 ('"values" false', 'values must be a list'),
                 ('"values" 0', 'values must be a list')]
        for argument, error in cases:
            with self.subTest(argument=argument):
                template.write_text('{{ include "homelab.common.tplvalues.merge" '
                                    '(dict "context" . ' + argument + ') }}')
                self.assertIn(error, self.render(chart=consumer, ok=False))

    def test_pull_secrets_in_pod(self):
        consumer = self.work / 'pod-secrets'
        shutil.copytree(self.fixture, consumer)
        (consumer / 'templates/pod.yaml').write_text("""apiVersion: v1
kind: Pod
metadata:
  name: example
spec:
  {{- include "homelab.common.images.pullSecrets" (dict "global" .Values.global "pullSecrets" .Values.imagePullSecrets "images" (list .Values.image)) | nindent 2 }}
  containers:
    - name: example
      image: nginx:stable
""")
        for secrets, expected in [([], None), (['first'], [{'name': 'first'}]),
                                  (['first', {'name': 'second'}, 'first'],
                                   [{'name': 'first'}, {'name': 'second'}])]:
            with self.subTest(secrets=secrets):
                values = self.work / 'pod-values.yaml'
                values.write_text(yaml.safe_dump({'imagePullSecrets': secrets}))
                docs = yaml.safe_load_all(helm('template', 'demo', consumer, '-f', values))
                pod = next(doc for doc in docs if doc and doc['kind'] == 'Pod')
                self.assertEqual(pod['spec'].get('imagePullSecrets'), expected)
                if expected is None:
                    self.assertNotIn('imagePullSecrets', pod['spec'])
                self.assertEqual(pod['spec']['containers'],
                                 [{'name': 'example', 'image': 'nginx:stable'}])

    def test_optional_arguments_and_failures(self):
        consumer = self.work / 'optional'
        shutil.copytree(self.fixture, consumer)
        template = consumer / 'templates/configmap.yaml'
        template.write_text("""apiVersion: v1
kind: ConfigMap
metadata:
  name: optional
data:
  storage: {{ include "homelab.common.storage.class" (dict) | quote }}
  secrets: {{ include "homelab.common.images.pullSecrets" (dict) | quote }}
  account: {{ include "homelab.common.serviceAccount.name" (dict "context" .) | quote }}
  image: {{ include "homelab.common.images.image" (dict "imageRoot" (dict "repository" "nginx" "tag" "stable")) | quote }}
  merged: {{ include "homelab.common.tplvalues.merge" (dict "context" . "values" (list (dict "key" nil) (dict "key" "fallback"))) | quote }}
""")
        self.assertEqual(self.render(chart=consumer)['data'],
                         {'storage': '', 'secrets': '', 'account': 'default',
                          'image': 'nginx:stable', 'merged': 'key: null'})
        for expression, error in [
            ('include "homelab.common.images.image" (dict "imageRoot" (dict "repository" "nginx"))',
             'tag, digest or chart.AppVersion is required'),
            ('include "homelab.common.storage.claimName" (dict)',
             'existingClaim or defaultName is required'),
        ]:
            template.write_text('{{ ' + expression + ' }}')
            self.assertIn(error, self.render(chart=consumer, ok=False))

    def test_lint_package_and_coexistence(self):
        helm('lint', self.library, '--strict')
        helm('lint', self.fixture, '--strict')
        baseline = self.render()
        for archive in ARGS.common:
            with self.subTest(archive=archive):
                with tarfile.open(archive) as tar:
                    meta = yaml.safe_load(tar.extractfile('common/Chart.yaml'))
                consumer = self.work / ('consumer-' + meta['version'])
                shutil.copytree(self.fixture, consumer)
                shutil.copyfile(archive, consumer / 'charts' / archive.name)
                chart = yaml.safe_load((consumer / 'Chart.yaml').read_text())
                chart['dependencies'].append({'name': 'common', 'version': meta['version'],
                    'repository': 'https://charts.bitnami.com/bitnami'})
                (consumer / 'Chart.yaml').write_text(yaml.safe_dump(chart))
                (consumer / 'templates/common.yaml').write_text('''apiVersion: v1
kind: Secret
metadata:
  name: {{ include "common.names.fullname" . }}
stringData:
  image: {{ include "common.images.image" (dict "imageRoot" .Values.image "global" .Values.global) | quote }}
''')
                helm('lint', consumer, '--strict')
                self.assertEqual(self.render(chart=consumer), baseline)
                third_party = next(x for x in yaml.safe_load_all(helm('template', 'demo', consumer))
                                   if x and x['kind'] == 'Secret')
                self.assertEqual(third_party['metadata']['name'], 'demo-example')
                self.assertEqual(third_party['stringData']['image'], 'nginx:1.27')
                helm('package', consumer, '--destination', self.work)
                package = self.work / 'example-1.0.0+build.tgz'
                shutil.rmtree(consumer)
                self.assertEqual(self.render(chart=package), baseline)
                with tarfile.open(package) as tar:
                    names = tar.getnames()
                    self.assertIn('example/charts/homelab-common/LICENSE', names)
                    self.assertIn('example/charts/homelab-common/NOTICE', names)
                    self.assertIn('example/charts/common/Chart.yaml', names)
                    self.assertFalse(any('/tests/' in x or '.serena' in x for x in names))
        helm('package', self.library, '--destination', self.work)
        with tarfile.open(self.work / 'homelab-common-0.1.0.tgz') as tar:
            self.assertFalse(any('/charts/' in n for n in tar.getnames()))
            self.assertEqual(yaml.safe_load(tar.extractfile('homelab-common/Chart.yaml'))['type'], 'library')
        print('Helm:', helm('version', '--short').strip())
        for archive in ARGS.common:
            print('Coexistence artifact:', archive.name, hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main(argv=['test.py'], verbosity=2)
