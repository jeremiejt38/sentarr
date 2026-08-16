from sentarr.collectors.transmission import _map_status


def test_map_status_error() -> None:
    assert _map_status(4, 1) == "error"
    assert _map_status(6, 1) == "error"


def test_map_status_paused() -> None:
    assert _map_status(0, 0) == "paused"


def test_map_status_queued() -> None:
    assert _map_status(1, 0) == "queued"
    assert _map_status(2, 0) == "queued"
    assert _map_status(3, 0) == "queued"


def test_map_status_downloading() -> None:
    assert _map_status(4, 0) == "downloading"


def test_map_status_checking() -> None:
    assert _map_status(5, 0) == "checking"


def test_map_status_seeding() -> None:
    assert _map_status(6, 0) == "seeding"


def test_map_status_unknown() -> None:
    assert _map_status(7, 0) == "unknown"
    assert _map_status(-1, 0) == "unknown"
