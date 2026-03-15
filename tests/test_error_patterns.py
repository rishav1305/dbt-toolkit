"""Tests for error pattern matching."""

from scripts.error_patterns import match_error


def test_match_relation_not_found():
    error = 'Runtime Error: relation "schema.model_name" does not exist'
    match = match_error(error)
    assert match is not None
    assert match.category == "runtime_sql"
    assert "does not exist" in match.pattern
    assert len(match.suggestions) > 0


def test_match_permission_denied():
    error = "permission denied for relation stg_users"
    match = match_error(error)
    assert match is not None
    assert match.category == "permission"


def test_match_compilation_error():
    error = "Compilation Error in model my_model: 'ref' is undefined"
    match = match_error(error)
    assert match is not None
    assert match.category == "compilation"


def test_match_connection_refused():
    error = "could not connect to server: Connection refused"
    match = match_error(error)
    assert match is not None
    assert match.category == "connection"


def test_match_timeout():
    error = "Statement timeout: canceling statement due to statement timeout"
    match = match_error(error)
    assert match is not None
    assert match.category == "performance"


def test_match_duplicate_key():
    error = "duplicate key value violates unique constraint"
    match = match_error(error)
    assert match is not None
    assert match.category == "runtime_sql"


def test_match_redshift_spectrum():
    error = 'Relation "tmp_spectrum_scan" already exists'
    match = match_error(error)
    assert match is not None
    assert match.category == "redshift"


def test_match_yaml_parse():
    error = "YAMLError: mapping values are not allowed here"
    match = match_error(error)
    assert match is not None
    assert match.category == "parse"


def test_match_missing_ref():
    error = "Compilation Error: Node model.proj.missing_ref not found"
    match = match_error(error)
    assert match is not None
    assert match.category == "compilation"


def test_no_match_unknown_error():
    error = "Something completely unexpected happened with no known pattern"
    match = match_error(error)
    assert match is None


def test_match_returns_suggestions():
    error = 'relation "schema.table" does not exist'
    match = match_error(error)
    assert match is not None
    assert isinstance(match.suggestions, list)
    assert len(match.suggestions) >= 1


def test_match_disk_full():
    error = "No space left on device"
    match = match_error(error)
    assert match is not None
    assert match.category == "runtime_sql"
