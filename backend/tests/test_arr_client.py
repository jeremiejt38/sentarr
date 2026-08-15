import pytest
import respx
from httpx import Response

from sentarr.collectors.arr_client import ArrClient, ArrClientError


@respx.mock
def test_get_queue_success() -> None:
    with respx.mock:
        route = respx.get("http://radarr.test/api/v3/queue").mock(
            return_value=Response(200, json={"records": []})
        )
        client = ArrClient("radarr-test", "http://radarr.test", "secret", "radarr")
        result = client.get_queue()
        assert result == {"records": []}
        assert route.called
        client.close()


@respx.mock
def test_get_queue_error_raises() -> None:
    with respx.mock:
        respx.get("http://radarr.test/api/v3/queue").mock(return_value=Response(500))
        client = ArrClient("radarr-test", "http://radarr.test", "secret", "radarr")
        with pytest.raises(ArrClientError):
            client.get_queue()
        client.close()


def test_non_get_method_rejected() -> None:
    client = ArrClient("radarr-test", "http://radarr.test", "secret", "radarr")
    with pytest.raises(ArrClientError):
        client._request("POST", "/movie")
    client.close()
