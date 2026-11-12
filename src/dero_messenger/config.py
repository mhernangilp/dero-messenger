"""Nonsecret profile configuration; wallet credentials remain in the environment."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .storage import private_directory


@dataclass
class Config:
    address: str
    backend: str = "simulated"
    chain: str = ".demo/chain.db"
    wallet_rpc: str = "http://127.0.0.1:20209/json_rpc"
    confirmations: int = 10
    enable_mainnet: bool = False
    fee_atomic: int = 121
    spending_policy: str | None = None

    def save(self, profile: Path) -> None:
        private_directory(profile)
        path = profile / "config.json"
        if path.exists():
            raise ValueError("Profile already exists")
        with path.open("x") as file:
            file.write(json.dumps(asdict(self), indent=2) + "\n")
        path.chmod(0o600)

    @classmethod
    def load(cls, profile: Path) -> "Config":
        return cls(**json.loads((profile / "config.json").read_text()))
