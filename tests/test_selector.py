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


# --- Advanced selector tests ---


def test_upstream_depth():
    result = build_select_string(models=["model_a"], include_upstream=True, upstream_depth=2)
    assert result == "2+model_a"


def test_downstream_depth():
    result = build_select_string(models=["model_a"], include_downstream=True, downstream_depth=3)
    assert result == "model_a+3"


def test_at_operator():
    result = build_select_string(models=["model_a"], at_operator=True)
    assert result == "@model_a"


def test_config_selector():
    result = build_select_string(configs=["materialized:incremental"])
    assert result == "config.materialized:incremental"


def test_source_selector():
    result = build_select_string(sources=["schema_name.table_a"])
    assert result == "source:schema_name.table_a"


def test_resource_type():
    result = build_select_string(resource_types=["model"])
    assert result == "resource_type:model"


def test_test_type():
    result = build_select_string(test_types=["unit"])
    assert result == "test_type:unit"


def test_exclusion():
    select, exclude = build_select_string(
        tags=["daily"],
        exclude_models=["model_slow"],
        return_exclude=True,
    )
    assert select == "tag:daily"
    assert exclude == "model_slow"


def test_complex_selection():
    result = build_select_string(
        models=["stg_model"],
        tags=["daily"],
        include_downstream=True,
        downstream_depth=1,
    )
    assert "stg_model+1" in result
    assert "tag:daily" in result
