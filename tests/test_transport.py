import pytest

from dero_messenger import protocol as p
from dero_messenger.rpc import RPC, RPCError
from dero_messenger.transport import Dero
from dero_messenger.wallet import Wallet


class FakeRPC:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        address = "dero1" + "q" * 61
        return {
            "GetAddress": {"address": address},
            "GetHeight": {"height": 20},
            "MakeIntegratedAddress": {"integrated_address": address, "payload_rpc": []},
            "Transfer": {"txid": "abc"},
            "GetTransfers": {
                "entries": [
                    {
                        "incoming": True,
                        "height": 10,
                        "txid": "abc",
                        "pos": 0,
                        "payload_rpc": p.payload_rpc(b"packet"),
                    },
                    {"incoming": True, "payload_rpc": []},
                ]
            },
        }[method]


def test_wallet_rpc_contract_confirmation_and_payload():
    rpc = FakeRPC()
    wallet = Wallet(rpc)
    address = wallet.address()
    dero = Dero(wallet, address)
    with pytest.raises(ValueError, match="disabled"):
        dero.send(address, b"packet")
    dero.enabled = True
    with pytest.raises(ValueError, match="confirmed"):
        dero.send(address, b"packet")
    prompts = []
    dero.confirm = lambda text: prompts.append(text) or True
    assert dero.send(address, b"packet") == "abc"
    assert "amount 1 atomic" in prompts[0]
    call = [params for method, params in rpc.calls if method == "Transfer"][0]
    assert call["transfers"][0]["amount"] == 1
    assert call["ringsize"] == 16
    height, incoming = dero.incoming()
    assert height == 20
    assert incoming[0].confirmations == 11
    assert incoming[0].payload == b"packet"
    with pytest.raises(ValueError):
        dero.send(address, bytes(103))


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/json_rpc",
        "http://0.0.0.0/json_rpc",
        "http://localhost/json_rpc",
        "http://127.0.0.1/redirect",
        "http://user:secret@127.0.0.1/json_rpc",
    ],
)
def test_rpc_requires_explicit_loopback(url):
    with pytest.raises(ValueError):
        RPC(url)


def test_jsonrpc_http_contract(monkeypatch):
    import httpx

    original = httpx.Client
    calls = []

    def handler(request):
        import json

        body = json.loads(request.content)
        calls.append(body)
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": body["id"], "result": {"height": 42}}
        )

    monkeypatch.setattr(
        httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw)
    )
    assert RPC("http://127.0.0.1:20209/json_rpc").call("GetHeight") == {"height": 42}
    assert calls[0]["method"] == "GetHeight"
    assert "params" not in calls[0]
    RPC("http://127.0.0.1:20209/json_rpc").call("GetBalance", {})
    assert calls[1]["params"] == {}


def test_rpc_failure_never_retries(monkeypatch):
    import httpx

    original = httpx.Client
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("ambiguous")

    monkeypatch.setattr(
        httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw)
    )
    with pytest.raises(RPCError):
        RPC("http://127.0.0.1:20209/json_rpc").call("Transfer")
    assert len(calls) == 1


def test_dero_pacing_waits_for_official_history():
    class HistoryRPC:
        def __init__(self):
            self.indexed = False

        def call(self, method, params):
            assert method == "GetTransferbyTXID"
            if not self.indexed:
                raise RPCError("Transaction not found", not_found=True)
            return {"entry": {"txid": params["txid"], "height": 10}}

    rpc = HistoryRPC()
    transport = Dero(Wallet(rpc), "unused")
    assert not transport.ready("txid")
    rpc.indexed = True
    assert transport.ready("txid")


def test_pacing_does_not_hide_authentication_failure():
    class FailedRPC:
        def call(self, method, params):
            raise RPCError("Wallet RPC HTTP status 401")

    with pytest.raises(RPCError, match="401"):
        Dero(Wallet(FailedRPC()), "unused").ready("txid")
