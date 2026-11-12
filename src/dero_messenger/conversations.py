"""Transactional conversation state machine and recoverable outbox."""

import hashlib
import logging
import os
import time

from cryptography.exceptions import InvalidSignature, InvalidTag

from . import crypto
from . import protocol as p
from .storage import Store
from .transport import Transport

LOG = logging.getLogger(__name__)
MAX_SESSIONS = 128
MAX_MESSAGES = 10000
MAX_COUNTER = 10000
MAX_AGE = 30 * 86400


def initial_state(address: str) -> dict:
    return dict(
        address=address,
        identity=crypto.identity().hex(),
        contacts={},
        sessions={},
        fragments={},
        deferred={},
        seen={},
        outbox=[],
        messages=[],
        height=0,
    )


class Messenger:
    def __init__(self, store: Store, transport: Transport, confirmations: int = 1):
        self.store, self.transport = store, transport
        if confirmations < 1:
            raise ValueError("At least one confirmation is required")
        self.confirmations = confirmations

    def identity(self) -> dict:
        key = crypto.public(bytes.fromhex(self.store.snapshot()["identity"]))
        return {"public_key": key.hex(), "fingerprint": crypto.fingerprint(key)}

    def add_contact(self, address: str, alias: str, public_key: str) -> None:
        self.transport.validate(address)
        key = bytes.fromhex(public_key)
        public_key = key.hex()
        if len(key) != 32 or not alias or len(alias) > 80:
            raise ValueError("Provide a 32-byte identity key and a short alias")
        with self.store.transaction() as state:
            if address == state["address"] or public_key == self.identity_key(state).hex():
                raise ValueError("Cannot add self as contact")
            old = state["contacts"].get(address)
            if old and old["identity"] != public_key:
                raise ValueError("Identity changes require a new profile in this PoC")
            if any(c["alias"] == alias and a != address for a, c in state["contacts"].items()):
                raise ValueError("Alias already exists")
            if len(state["contacts"]) >= 128 and not old:
                raise ValueError("Contact quota reached")
            state["contacts"][address] = {"alias": alias, "identity": public_key}

    @staticmethod
    def identity_key(state: dict) -> bytes:
        return crypto.public(bytes.fromhex(state["identity"]))

    @staticmethod
    def resolve(state: dict, contact: str) -> str:
        if contact in state["contacts"]:
            return contact
        for address, value in state["contacts"].items():
            if value["alias"] == contact:
                return address
        raise ValueError("Unknown contact; add and verify its identity first")

    @staticmethod
    def queue(state: dict, address: str, envelope: bytes) -> None:
        packets = p.fragments(envelope)
        if len(state["outbox"]) + len(packets) > 2048:
            raise ValueError("Outbox quota reached")
        for packet in packets:
            state["outbox"].append(
                dict(
                    destination=address,
                    payload=packet.hex(),
                    status="pending",
                    txid=None,
                    envelope_id=hashlib.sha256(envelope).hexdigest(),
                )
            )

    def request(self, contact: str, *, prepare_only: bool = False) -> str:
        with self.store.transaction() as state:
            address = self.resolve(state, contact)
            if len(state["sessions"]) >= MAX_SESSIONS:
                raise ValueError("Session quota reached; use a new profile")
            secret, eph = crypto.ephemeral()
            sid = os.urandom(16)
            req = p.request(
                bytes.fromhex(state["identity"]),
                sid,
                bytes.fromhex(state["contacts"][address]["identity"]),
                eph,
                state["address"],
                address,
            )
            state["sessions"][sid.hex()] = dict(
                status="requested", peer=address, request=req.hex(), ephemeral=secret.hex()
            )
            self.queue(state, address, req)
        if not prepare_only:
            self.flush()
        return sid.hex()

    @staticmethod
    def establish(session: dict, first: bytes, second: bytes, initiator: bool) -> None:
        session.update(
            status="established",
            tx=(first if initiator else second).hex(),
            rx=(second if initiator else first).hex(),
            counter=0,
            received=[],
            established=time.time(),
        )
        session.pop("ephemeral", None)

    def accept(self, sid: str, *, prepare_only: bool = False) -> None:
        with self.store.transaction() as state:
            session = state["sessions"].get(sid)
            if session is None or session["status"] != "incoming":
                raise ValueError("No pending request with this identifier")
            req = bytes.fromhex(session["request"])
            parsed = p.parse_request(req)
            contact = state["contacts"].get(session["peer"])
            if not contact or contact["identity"] != parsed["identity"].hex():
                raise ValueError("Add the sender and verify its fingerprint before accepting")
            secret, eph = crypto.ephemeral()
            response = p.accept(bytes.fromhex(state["identity"]), req, eph)
            first, second = crypto.derive(secret, parsed["ephemeral"], req + response)
            self.establish(session, first, second, False)
            self.queue(state, session["peer"], response)
        if not prepare_only:
            self.flush()

    def reject(self, sid: str) -> None:
        with self.store.transaction() as state:
            session = state["sessions"].get(sid)
            if not session or session["status"] != "incoming":
                raise ValueError("No pending request")
            session["status"] = "rejected"

    def send(self, contact: str, text: str, *, prepare_only: bool = False) -> None:
        plaintext = text.encode()
        if not 1 <= len(plaintext) <= p.MAX_TEXT:
            raise ValueError("Message must contain 1 to 4096 UTF-8 bytes")
        with self.store.transaction() as state:
            address = self.resolve(state, contact)
            candidates = [
                (sid, s)
                for sid, s in state["sessions"].items()
                if s["peer"] == address and s["status"] == "established"
            ]
            if not candidates:
                raise ValueError("No established session")
            sid, session = max(candidates, key=lambda item: item[1]["established"])
            if session["counter"] >= MAX_COUNTER or time.time() - session["established"] > MAX_AGE:
                raise ValueError("Session send limit reached; request a new session")
            if len(state["messages"]) >= MAX_MESSAGES:
                raise ValueError("Message quota reached")
            count = session["counter"]
            aad = p.header(p.MESSAGE, bytes.fromhex(sid)) + count.to_bytes(8, "big")
            envelope = aad + crypto.encrypt(bytes.fromhex(session["tx"]), count, plaintext, aad)
            session["counter"] += 1
            self.queue(state, address, envelope)
            state["messages"].append(
                dict(
                    peer=address,
                    direction="out",
                    text=text,
                    sid=sid,
                    counter=count,
                    status="queued",
                    envelope_id=hashlib.sha256(envelope).hexdigest(),
                )
            )
        # Ciphertext and incremented counter are durable before any transmission.
        if not prepare_only:
            self.flush()

    def flush(self, retry_uncertain: bool = False) -> None:
        # Serialize sends under the DB lock. An interrupted RPC leaves 'sending'
        # durable; recovery requires explicit retry because submission is ambiguous.
        with self.store.transaction() as state:
            if retry_uncertain:
                for item in state["outbox"]:
                    if item["status"] == "sending":
                        item["status"] = "pending"
        while True:
            with self.store.transaction() as state:
                index = next(
                    (i for i, x in enumerate(state["outbox"]) if x["status"] == "pending"), None
                )
                if index is None:
                    return
                if any(x["status"] == "sending" for x in state["outbox"]):
                    raise ValueError("Uncertain submission blocks outbox; reconcile before retry")
                previous = next(
                    (x["txid"] for x in reversed(state["outbox"][:index]) if x["txid"]), None
                )
                if previous and not self.transport.ready(previous):
                    return
                state["outbox"][index]["status"] = "sending"
            with self.store.transaction() as state:
                item = state["outbox"][index]
                if item["status"] != "sending":
                    continue
                item["txid"] = self.transport.send(
                    item["destination"], bytes.fromhex(item["payload"])
                )
                item["status"] = "submitted"
                for message in state["messages"]:
                    matching = [
                        x
                        for x in state["outbox"]
                        if x.get("envelope_id") == message.get("envelope_id")
                    ]
                    if matching and all(x["status"] == "submitted" for x in matching):
                        message["status"] = "submitted"

    def receive(self, state: dict, envelope: bytes) -> str | None:
        kind, raw_sid = p.parse_header(envelope)
        sid = raw_sid.hex()
        session = state["sessions"].get(sid)
        if kind == p.REQUEST:
            parsed = p.parse_request(envelope)
            if (
                parsed["target"] != self.identity_key(state)
                or parsed["destination"] != state["address"]
            ):
                raise ValueError("Request addressed to a different participant")
            if session:
                return None
            if len(state["sessions"]) >= MAX_SESSIONS:
                raise ValueError("Session quota reached")
            self.transport.validate(parsed["source"])
            state["sessions"][sid] = dict(
                status="incoming", peer=parsed["source"], request=envelope.hex()
            )
            return f"Conversation request {sid}"
        if not session:
            raise ValueError("Unknown session")
        if kind == p.ACCEPT:
            if session["status"] != "requested":
                return None
            req = bytes.fromhex(session["request"])
            eph = p.parse_accept(envelope, req)
            first, second = crypto.derive(bytes.fromhex(session["ephemeral"]), eph, req + envelope)
            self.establish(session, first, second, True)
            return f"Session established {sid}"
        if session["status"] != "established" or len(envelope) < 43:
            raise ValueError("Message without established session")
        count = int.from_bytes(envelope[18:26], "big")
        if count >= MAX_COUNTER or count in session["received"]:
            raise ValueError("Replayed or out-of-range counter")
        plaintext = crypto.decrypt(
            bytes.fromhex(session["rx"]), count, envelope[26:], envelope[:26]
        )
        if not 1 <= len(plaintext) <= p.MAX_TEXT:
            raise ValueError("Invalid plaintext length")
        text = plaintext.decode("utf-8")
        if len(state["messages"]) >= MAX_MESSAGES:
            raise ValueError("Message quota reached")
        session["received"].append(count)
        state["messages"].append(
            dict(
                peer=session["peer"],
                direction="in",
                text=text,
                sid=sid,
                counter=count,
                status="confirmed",
            )
        )
        return f"Message received in {sid}"

    def drain(self, state: dict) -> list[str]:
        events = []
        for mid, item in list(state["deferred"].items()):
            if time.time() - item["created"] > p.TTL:
                del state["deferred"][mid]
        for _ in range(3):
            progressed = False
            for mid, item in list(state["deferred"].items()):
                envelope = bytes.fromhex(item["envelope"])
                try:
                    kind, sid = p.parse_header(envelope)
                    session = state["sessions"].get(sid.hex())
                    if kind == p.MESSAGE and (not session or session["status"] == "requested"):
                        continue
                    event = self.receive(state, envelope)
                    if event:
                        events.append(event)
                except (ValueError, InvalidSignature, InvalidTag, UnicodeError) as exc:
                    LOG.warning("incoming_rejected", extra={"reason": type(exc).__name__})
                del state["deferred"][mid]
                progressed = True
            if not progressed:
                break
        return events

    def sync(self) -> list[str]:
        height, transfers = self.transport.incoming()
        events = []
        with self.store.transaction() as state:
            # Full-history scans avoid conflating block height with topoheight and
            # recover late wallet indexing. Bounded inbox, no false finality promise.
            for transfer in transfers:
                if transfer.confirmations < self.confirmations:
                    continue
                if transfer.key in state["seen"]:
                    state["seen"][transfer.key]["confirmations"] = transfer.confirmations
                    continue
                if len(state["seen"]) >= 100000:
                    raise ValueError("Inbox quota reached; archive profile")
                try:
                    envelope = p.reconstruct(state["fragments"], transfer.payload)
                    if envelope:
                        if len(state["deferred"]) >= 64:
                            raise ValueError("Deferred envelope quota reached")
                        mid = hashlib.sha256(envelope).hexdigest()
                        state["deferred"].setdefault(
                            mid, dict(envelope=envelope.hex(), created=time.time())
                        )
                except (ValueError, InvalidSignature, InvalidTag, UnicodeError) as exc:
                    LOG.warning("incoming_rejected", extra={"reason": type(exc).__name__})
                state["seen"][transfer.key] = dict(
                    height=transfer.height,
                    confirmations=transfer.confirmations,
                    reported_sender=transfer.reported_sender,
                    fee_atomic=transfer.fee_atomic,
                    topoheight=transfer.topoheight,
                    blockhash=transfer.blockhash,
                    timestamp=transfer.timestamp,
                    observed_at=time.time(),
                    packet_sha256=hashlib.sha256(transfer.payload).hexdigest(),
                    fragment_id=transfer.payload[2:18].hex(),
                )
            events.extend(self.drain(state))
            state["height"] = height
        return events
