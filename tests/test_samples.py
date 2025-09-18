import json, os

def test_samples_exist():
    base = os.path.join(os.path.dirname(__file__), "data")
    assert os.path.exists(os.path.join(base, "textract_sample.json"))
