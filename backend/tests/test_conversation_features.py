"""Database upgrade, saved preferences, and replay integration without live services."""
import importlib.util
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import test_personality


class ConversationFeatureTests(unittest.TestCase):
    setUp = test_personality.PersonalityTests.setUp

    def test_legacy_upgrade_preserves_rows_and_replay_metadata(self):
        with sqlite3.connect(self.memory.PATH_TO_MEMORY) as conn:
            conn.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)')
            conn.execute("INSERT INTO messages VALUES (7, 'assistant', 'Legacy reply', '2026-09-01 12:00')")
        rows = self.memory.load_memory_raw()
        self.assertEqual(rows[0], dict(id=7, role='assistant', content='Legacy reply',
                                      created_at='2026-09-01 12:00', can_replay=False))
        message_id = self.memory.append_message('assistant', 'Hello', japanese='こんにちは')
        self.assertGreater(message_id, 7)
        self.assertEqual(self.memory.get_message_voice(message_id), ('こんにちは', None))
        self.assertTrue(self.memory.load_memory_raw()[-1]['can_replay'])
        self.assertEqual(self.client.get('/message_audio/7').status_code, 404)
        self.assertEqual(self.client.get('/message_audio/999').status_code, 404)
        self.assertEqual(self.client.head(f'/message_audio/{message_id}').status_code, 405)

    def test_settings_validation_persistence_and_budget_does_not_delete_history(self):
        prefs = self.api.preferences
        with patch.object(prefs, 'PATH', Path(self.directory.name) / 'settings.json'):
            self.assertEqual(self.client.get('/conversation_settings').json['context_budget'], 40000)
            valid = {'context_budget': 500, 'voice_retention': 2}
            self.assertEqual(self.client.post('/conversation_settings', json=valid).json, valid)
            for bad in ([], {}, {**valid, 'context_budget': True}, {**valid, 'voice_retention': 0},
                        {**valid, 'context_budget': 500.5}):
                self.assertEqual(self.client.post('/conversation_settings', json=bad).status_code, 400)
            self.assertEqual(self.client.get('/conversation_settings').json, valid)
            self.memory.append_message('user', 'Old message ' * 1000)
            self.memory.append_message('assistant', 'Old reply')
            self.memory.append_message('user', 'Newest message')
            prompt = prefs.trim_history(self.memory.build_prompt_messages(), 500)
            self.assertEqual(prompt, [{'role': 'user', 'content': 'Newest message'}])
            self.assertEqual(len(self.memory.load_memory_raw()), 3)
            large = [{'role': 'user', 'content': '日本語' * 1000}]
            self.assertEqual(prefs.trim_history(large, 500), large)

    def test_message_route_stores_voice_and_replay_does_not_call_llm(self):
        reply = self.chat.AmadeusPack(assistant_reply_ENG='Hello', assistant_reply_JPS='こんにちは')
        with patch.object(self.api, 'has_api_key', return_value=True), patch.object(
                self.chat, 'getResponsePacked', return_value=reply) as llm:
            response = self.client.post('/', json={'user_input': 'Hi'})
            self.assertEqual(response.status_code, 200)
            id = response.json['message_id']
            self.assertEqual(self.memory.get_message_voice(id), ('こんにちは', None))
            with patch.object(self.api, 'streamVoiceChunks', return_value=(chunk for chunk in (b'RIFF', b'pcm'))) as tts:
                replay = self.client.get(f'/message_audio/{id}')
                self.assertEqual(replay.data, b'RIFFpcm')
                tts.assert_called_once()
            self.assertEqual(llm.call_count, 1)
        self.memory.reset_memory()
        self.assertEqual(self.client.get(f'/message_audio/{id}').status_code, 404)

    def test_cache_reuse_retention_and_interrupted_stream(self):
        spec = importlib.util.spec_from_file_location('replay_tts', Path(__file__).resolve().parents[1] / 'tts.py')
        tts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tts)
        tts.OUT_WAV = Path(self.directory.name) / 'generated' / 'generated.wav'
        class Upstream:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def raise_for_status(self): pass
            def iter_content(self, **kwargs): yield from (b'RIFF', b'pcm')
        with patch.object(tts, '_request_payload', return_value={}), patch.object(
                tts.requests, 'post', side_effect=lambda *a, **kw: Upstream()) as post:
            self.assertEqual(b''.join(tts.streamVoiceChunks('first', 1, 1)), b'RIFFpcm')
            self.assertEqual(b''.join(tts.streamVoiceChunks('first', 1, 1)), b'RIFFpcm')
            self.assertEqual(post.call_count, 1)
            b''.join(tts.streamVoiceChunks('different text after database replacement', 1, 1))
            self.assertEqual(post.call_count, 2)
            b''.join(tts.streamVoiceChunks('second', 2, 1))
            self.assertFalse(list((tts.OUT_WAV.parent / 'voices').glob('1-*.wav')))
            chunks = tts.streamVoiceChunks('interrupted', 3, 1)
            next(chunks)
            chunks.close()
            self.assertFalse(list((tts.OUT_WAV.parent / 'voices').glob('3-*.wav')))
            self.assertFalse(list((tts.OUT_WAV.parent / 'voices').glob('3-*.tmp')))
            self.assertFalse(tts._speech_lock.locked())
            b''.join(tts.streamVoiceChunks('first again', 1, 1))
            self.assertTrue(list((tts.OUT_WAV.parent / 'voices').glob('1-*.wav')))
