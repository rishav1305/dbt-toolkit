# tests/test_selector.py
from scripts.selector import build_select_string


def test_single_model_name():
    result = build_select_string(models=["stg_wcbm_audience_metrics"])
    assert result == "stg_wcbm_audience_metrics"


def test_multiple_models():
    result = build_select_string(models=["model_a", "model_b"])
    assert result == "model_a model_b"


def test_tag_selector():
    result = build_select_string(tags=["daily"])
    assert result == "tag:daily"


def test_multiple_tags_intersection():
    result = build_select_string(tags=["daily", "finance"])
    assert result == "tag:daily,tag:finance"


def test_path_selector():
    result = build_select_string(paths=["models/staging"])
    assert result == "path:models/staging"


def test_with_upstream():
    result = build_select_string(models=["model_a"], include_upstream=True)
    assert result == "+model_a"


def test_with_downstream():
    result = build_select_string(models=["model_a"], include_downstream=True)
    assert result == "model_a+"


def test_with_both():
    result = build_select_string(models=["model_a"], include_upstream=True, include_downstream=True)
    assert result == "+model_a+"


def test_combined_tag_and_path():
    result = build_select_string(tags=["daily"], paths=["models/staging"])
    assert result == "tag:daily path:models/staging"


def test_full_refresh_model():
    result = build_select_string(models=["model_a"], include_downstream=True)
    assert result == "model_a+"
