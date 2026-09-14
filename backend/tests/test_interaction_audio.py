"""Test selection/memory pairing without loading the LLM or TTS."""
import ast
from pathlib import Path
import random
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class InteractionAudioTests(unittest.TestCase):
    def test_variants_remain_paired(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'chat.py').read_text())
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in
                  {'INTERACTION_EVENTS', 'INTERACTION_RESPONSES'} for t in n.targets)) or
                 (isinstance(n, ast.FunctionDef) and n.name == 'SpecialInteraction')]
        messages = []
        scope = {'store': SimpleNamespace(append_message=lambda role, text, **kwargs: messages.append((role, text))), 'random': random}
        scope.update(runpy.run_path(str(Path(__file__).resolve().parents[1] / 'chat_interactions.py')))
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'chat.py', 'exec'), scope)
        for interaction_id, variants in scope['INTERACTION_RESPONSES'].items():
            for variant in variants:
                messages.clear()
                with patch.object(random, 'choice', return_value=variant):
                    reply = scope['SpecialInteraction'](interaction_id)
                self.assertEqual(reply['response'], variant['text'])
                self.assertEqual(reply['audio_url'], variant['audio_url'])
                self.assertEqual(messages[-1], ('assistant', variant['text']))
        variant = {'text': 'Example text', 'audio_url': '/audio/example.wav'}
        with patch.object(random, 'choice', return_value=variant):
            self.assertEqual(scope['SpecialInteraction'](2), {'response': 'Example text', 'audio_url': '/audio/example.wav', 'message_id': None})
        messages.clear()
        with self.assertRaises(ValueError): scope['SpecialInteraction'](999)
        self.assertEqual(messages, [])


if __name__ == '__main__': unittest.main()
