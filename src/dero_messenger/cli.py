"""Interactive CLI. Secrets are prompted, never accepted as command arguments."""

import json
import logging
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from cryptography.exceptions import InvalidTag
from rich.console import Console

from . import crypto, protocol
from .config import Config
from .conversations import Messenger, initial_state
from .experiment import SpendingGate
from .monitor import listen
from .rpc import RPC, RPCError
from .storage import Store
from .transport import Dero, Simulated, wallet_auth
from .wallet import Wallet

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
contacts = typer.Typer(no_args_is_help=True)
chat = typer.Typer(no_args_is_help=True)
wallet = typer.Typer(no_args_is_help=True)
app.add_typer(contacts, name="contacts")
app.add_typer(chat, name="chat")
app.add_typer(wallet, name="wallet")
console = Console(markup=False, highlight=False)


def display(value: object) -> None:
    # Escape terminal control characters from untrusted aliases and messages.
    text = str(value)
    console.print("".join(c if c.isprintable() or c == "\n" else f"\\x{ord(c):02x}" for c in text))


@app.callback()
def main(
    ctx: typer.Context, profile: Annotated[Path, typer.Option()] = Path(".demo/alice")
) -> None:
    """Encrypted messaging research PoC; simulation is the default."""
    os.umask(0o077)
    logging.basicConfig(format='{"event":"%(message)s","level":"%(levelname)s"}')
    ctx.obj = profile.resolve()


def passphrase() -> str:
    return os.getenv("DERO_CHAT_PASSPHRASE") or typer.prompt("Profile passphrase", hide_input=True)


@contextmanager
def opened(ctx: typer.Context) -> Iterator[Messenger]:
    store = None
    transport = None
    gate = None
    try:
        config = Config.load(ctx.obj)
        store = Store(ctx.obj / "state.db", passphrase())
        if config.backend == "simulated":
            transport = Simulated(Path(config.chain), config.address)
        elif config.backend == "dero":
            if config.spending_policy:
                policy_path = Path(config.spending_policy).resolve()
                gate = SpendingGate(
                    policy_path.with_suffix(".db"), json.loads(policy_path.read_text())
                )
            transport = Dero(
                Wallet(RPC(config.wallet_rpc, wallet_auth())),
                config.address,
                config.enable_mainnet,
                config.fee_atomic,
                typer.confirm,
                gate,
            )
        else:
            raise ValueError("Unsupported transport backend")
        yield Messenger(store, transport, config.confirmations)
    except InvalidTag:
        display("Error: incorrect passphrase or damaged encrypted profile")
        raise typer.Exit(1) from None
    except (ValueError, RPCError, OSError, sqlite3.Error) as exc:
        display(f"Error: {exc}")
        raise typer.Exit(1) from None
    finally:
        if gate:
            gate.close()
        if store:
            store.close()
        if isinstance(transport, Simulated):
            transport.db.close()


@app.command()
def setup(
    ctx: typer.Context,
    address: Annotated[str, typer.Option()] = "sim:alice",
    backend: Annotated[str, typer.Option()] = "simulated",
    chain: Annotated[Path, typer.Option()] = Path(".demo/chain.db"),
    wallet_rpc: Annotated[str, typer.Option()] = "http://127.0.0.1:20209/json_rpc",
    enable_mainnet: Annotated[bool, typer.Option()] = False,
    confirmations: Annotated[int, typer.Option(min=1)] = 10,
    fee_atomic: Annotated[int, typer.Option(min=1, max=100000)] = 121,
    spending_policy: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Create an independent encrypted profile; DERO addresses come from Wallet RPC."""
    try:
        if (ctx.obj / "config.json").exists() or (ctx.obj / "state.db").exists():
            raise ValueError("Profile already exists")
        if backend == "dero":
            official = Wallet(RPC(wallet_rpc, wallet_auth()))
            address = official.address()
            official.validate(address)
        elif backend == "simulated":
            if enable_mainnet:
                raise ValueError("Mainnet flag requires the dero backend")
            Simulated.validate(None, address)
            confirmations = 1
        else:
            raise ValueError("Backend must be simulated or dero")
        secret = passphrase()
        config = Config(
            address,
            backend,
            str(chain.resolve()),
            wallet_rpc,
            confirmations,
            enable_mainnet,
            fee_atomic,
            str(spending_policy.resolve()) if spending_policy else None,
        )
        store = Store(ctx.obj / "state.db", secret, initial_state(address))
        key = crypto.public(bytes.fromhex(store.snapshot()["identity"]))
        store.close()
        config.save(ctx.obj)
        display(f"Profile created for {address}")
        display(f"Public identity: {key.hex()}")
        display(f"Fingerprint: {crypto.fingerprint(key)}")
    except (ValueError, RPCError, OSError) as exc:
        display(f"Error: {exc}")
        raise typer.Exit(1) from None


@app.command()
def identity(ctx: typer.Context) -> None:
    """Show the public application identity and verification fingerprint."""
    with opened(ctx) as messenger:
        display(json.dumps(messenger.identity()))


@wallet.command("status")
def wallet_status(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        if isinstance(messenger.transport, Dero):
            display(json.dumps(messenger.transport.wallet.status()))
        else:
            height, _ = messenger.transport.incoming()
            display(f"Simulated wallet: {messenger.store.snapshot()['address']}; height {height}")


@contacts.command("add")
def add(
    ctx: typer.Context,
    address: str,
    alias: Annotated[str, typer.Option()],
    identity: Annotated[str, typer.Option()],
    verified: Annotated[bool, typer.Option()] = False,
) -> None:
    """Pin an application identity after comparing fingerprints through a trusted channel."""
    with opened(ctx) as messenger:
        display(f"Application fingerprint: {crypto.fingerprint(bytes.fromhex(identity))}")
        if not verified and not typer.confirm("Have you independently verified this fingerprint?"):
            raise typer.Abort()
        messenger.add_contact(address, alias, identity)
        display("Contact saved. Application identity is not proof of wallet ownership.")


@contacts.command("list")
def list_contacts(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        for address, contact in messenger.store.snapshot()["contacts"].items():
            display(f"{contact['alias']}: {address} identity={contact['identity']}")


@chat.command("request")
def request(
    ctx: typer.Context,
    contact: str,
    prepare_only: Annotated[bool, typer.Option()] = False,
) -> None:
    """Create a request; --prepare-only persists it without calling the transport send path."""
    with opened(ctx) as messenger:
        display(messenger.request(contact, prepare_only=prepare_only))
        if prepare_only:
            display("Prepared locally; no transaction submitted. Review with chat proposal.")


@chat.command("proposal")
def proposal(ctx: typer.Context) -> None:
    """Display exact pending RPC parameters without sending or revealing private keys."""
    from .experiment import pending_proposal

    with opened(ctx) as messenger:
        config = Config.load(ctx.obj)
        display(
            json.dumps(pending_proposal(messenger.store.snapshot(), config.fee_atomic), indent=2)
        )


@chat.command("requests")
def requests(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        for sid, session in messenger.store.snapshot()["sessions"].items():
            if session["status"] == "incoming":
                req = protocol.parse_request(bytes.fromhex(session["request"]))
                display(
                    f"{sid}: claimed address {session['peer']}; "
                    f"identity {req['identity'].hex()}; "
                    f"fingerprint {crypto.fingerprint(req['identity'])}"
                )


@chat.command("accept")
def accept(
    ctx: typer.Context,
    request_id: str,
    prepare_only: Annotated[bool, typer.Option()] = False,
) -> None:
    with opened(ctx) as messenger:
        messenger.accept(request_id, prepare_only=prepare_only)
        display(
            "Accepted locally; response prepared without sending"
            if prepare_only
            else "Accepted; response queued or submitted"
        )


@chat.command("reject")
def reject(ctx: typer.Context, request_id: str) -> None:
    with opened(ctx) as messenger:
        messenger.reject(request_id)
        display("Request rejected locally")


@chat.command("send")
def send(
    ctx: typer.Context,
    contact: str,
    message: str,
    prepare_only: Annotated[bool, typer.Option()] = False,
) -> None:
    with opened(ctx) as messenger:
        messenger.send(contact, message, prepare_only=prepare_only)
        display(
            "Message encrypted and prepared locally; no transaction submitted"
            if prepare_only
            else "Message encrypted and queued; inspect chat outbox for submission status"
        )


@chat.command("read")
def read(ctx: typer.Context, contact: str) -> None:
    with opened(ctx) as messenger:
        state = messenger.store.snapshot()
        address = messenger.resolve(state, contact)
        for message in state["messages"]:
            if message["peer"] == address:
                display(f"{message['direction']}: {message['text']}")


@app.command("sync")
def sync(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        for event in messenger.sync():
            display(event)
        display(f"Synchronized wallet height {messenger.store.snapshot()['height']}")


@chat.command("listen")
def monitor(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        try:
            listen(messenger, display)
        except KeyboardInterrupt:
            display("Listener stopped")


@chat.command("outbox")
def outbox(ctx: typer.Context) -> None:
    with opened(ctx) as messenger:
        for item in messenger.store.snapshot()["outbox"]:
            display(f"{item['status']}: txid={item['txid']} destination={item['destination']}")


@chat.command("reconcile")
def reconcile(ctx: typer.Context) -> None:
    """Record known submitted packets in the app outbox using read-only wallet history."""
    with opened(ctx) as messenger:
        if not isinstance(messenger.transport, Dero):
            raise ValueError("Reconciliation requires the DERO backend")
        count = 0
        with messenger.store.transaction() as state:
            for item in state["outbox"]:
                if item["status"] not in ("pending", "sending"):
                    continue
                txid = messenger.transport.reconcile(
                    item["destination"], bytes.fromhex(item["payload"])
                )
                if txid:
                    item.update(status="submitted", txid=txid)
                    count += 1
        display(f"Reconciled {count} outbox fragments; no transactions submitted")


@chat.command("flush")
def flush(ctx: typer.Context, retry_uncertain: Annotated[bool, typer.Option()] = False) -> None:
    """Send pending fragments; uncertain paid submissions need manual reconciliation."""
    with opened(ctx) as messenger:
        if retry_uncertain and not typer.confirm(
            "Stop other profile processes and check Wallet RPC history first. "
            "Retrying an uncertain submission can pay twice. Retry?"
        ):
            raise typer.Abort()
        messenger.flush(retry_uncertain)
        display("Outbox checked; run chat flush again after the previous transfer is indexed")
