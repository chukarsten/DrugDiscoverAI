import unittest
from model_picker import find_smallest_local_model, pull_local_model, check_for_local_model

class TestModelPicker(unittest.TestCase):

    def test_finds_smallest(self):
        self.assertEqual(find_smallest_local_model({"smallest_model": 1, "medium_model": 2}), "smallest_model")

    def test_check_local_model(self):
        check_for_local_model("llama3.1")