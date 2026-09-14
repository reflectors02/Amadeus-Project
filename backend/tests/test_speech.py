"""Offline streaming checks: python -m unittest discover -s backend/tests."""
import ast
import importlib.util
from itertools import chain
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class SpeechTests(unittest.TestCase):
    def test_stream_cleanup(self):
        class Upstream:
            closed = False
            def __enter__(self): return self
            def __exit__(self, *args): self.closed = True
            def raise_for_status(self): pass
            def iter_content(self, **kwargs): yield from (b'RIFF', b'pcm')
        upstream = Upstream()
        requests = SimpleNamespace(post=lambda *a, **kw: upstream)
        with patch.dict(sys.modules, {'requests': requests}), tempfile.TemporaryDirectory() as directory:
            spec = importlib.util.spec_from_file_location('speech_tts_test', ROOT / 'tts.py')
            tts = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tts)
            tts.OUT_WAV = Path(directory) / 'generated.wav'
            tts._request_payload = lambda text: {'text': text}
            chunks = tts.streamVoiceChunks('test')
            self.assertEqual(next(chunks), b'RIFF')
            chunks.close()
            self.assertTrue(upstream.closed)
            self.assertFalse(tts._speech_lock.locked())
            self.assertFalse(tts.OUT_WAV.with_suffix('.browser.tmp').exists())
            self.assertEqual(b''.join(tts.streamVoiceChunks('test')), b'RIFFpcm')
            self.assertEqual(tts.OUT_WAV.read_bytes(), b'RIFFpcm')

    def test_speech_ticket(self):
        # Exercise the route body without importing LLM/TTS/Flask dependencies.
        tree = ast.parse((ROOT / 'api.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'speech')
        function.decorator_list = []
        class Response:
            def __init__(self, generator, **kwargs):
                self.generator = generator
                self.headers = {}
            def call_on_close(self, callback): self.close = callback
        tickets = {'one': (time.monotonic(), 'test', 1)}
        scope = dict(request=SimpleNamespace(method='GET'), _speech_requests=tickets,
                     _speech_requests_lock=threading.Lock(), time=time, chain=chain,
                     jsonify=lambda data: data, Response=Response,
                     streamVoiceChunks=lambda text, **kwargs: (chunk for chunk in (b'header', b'pcm')))
        voice = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_voice_response')
        scope.update(store=SimpleNamespace(get_message_voice=lambda id: ('test', None)),
                     preferences=SimpleNamespace(load=lambda: {'voice_retention': 100}))
        exec(compile(ast.Module(body=[function, voice], type_ignores=[]), 'api.py', 'exec'), scope)
        response = scope['speech']('one')
        self.assertEqual(scope['speech']('one')[1], 404)
        self.assertEqual(b''.join(response.generator), b'headerpcm')
        tickets['old'] = (time.monotonic() - 301, 'test', 1)
        self.assertEqual(scope['speech']('old')[1], 404)
        def fail(text, **kwargs):
            raise RuntimeError('upstream failure')
            yield
        scope['streamVoiceChunks'] = fail
        tickets['error'] = (time.monotonic(), 'test', 1)
        self.assertEqual(scope['speech']('error')[1], 502)


if __name__ == '__main__':
    unittest.main()
