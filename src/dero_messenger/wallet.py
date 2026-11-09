"""Official wallet RPC adapter; no wallet key generation or signing."""

from .rpc import RPC


class Wallet:
    def __init__(self, rpc: RPC):
        self.rpc = rpc

    def address(self) -> str:
        return self.rpc.call("GetAddress")["address"]

    def height(self) -> int:
        return int(self.rpc.call("GetHeight")["height"])

    def status(self) -> dict:
        return {
            "address": self.address(),
            "height": self.height(),
            **self.rpc.call("GetBalance", {}),
        }

    def validate(self, address: str) -> None:
        if not address.startswith("dero1") or len(address) != 66:
            raise ValueError("Only standard Mainnet DERO addresses are supported")
        # The official parser checks checksum, version, and curve point.
        result = self.rpc.call("MakeIntegratedAddress", {"address": address, "payload_rpc": []})
        if result.get("integrated_address") != address or result.get("payload_rpc"):
            raise ValueError("Invalid standard DERO address")

    def incoming(self) -> list[dict]:
        return (
            self.rpc.call(
                "GetTransfers",
                {
                    "in": True,
                    "out": False,
                    "coinbase": False,
                    "min_height": 0,
                },
            ).get("entries")
            or []
        )
