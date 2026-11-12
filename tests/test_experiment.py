import pytest

from dero_messenger.experiment import SpendingGate, message_count, plan

ADDRESSES = ["dero1" + c * 61 for c in "qpr"]  # Synthetic; never submitted to a wallet.


def policy():
    return dict(
        participants=dict.fromkeys(ADDRESSES, 2),
        max_transactions=2,
        max_debit_atomic=364,
        fee_atomic=181,
    )


def test_budget_and_message_boundaries():
    proposal = plan()
    assert proposal["transactions"] == 33
    assert proposal["max_debit_atomic"] == 6006
    assert proposal["per_wallet_debit_atomic"] == dict(alice=3094, bob=1456, charlie=1456)
    assert [message_count("x" * n) for n in (16, 17, 512, 4096)] == [1, 2, 10, 72]


def test_gate_limits_approval_and_restart(tmp_path):
    path = tmp_path / "budget.db"
    gate = SpendingGate(path, policy())
    calls = []

    def broadcast():
        calls.append(1)
        return "a" * 64

    args = (ADDRESSES[0], ADDRESSES[1], b"first", 181, 1000)
    with pytest.raises(ValueError, match="approval"):
        gate.submit(*args, False, broadcast)
    assert calls == []
    gate.submit(*args, True, broadcast)
    gate.close()
    gate = SpendingGate(path, policy())
    with pytest.raises(ValueError, match="already"):
        gate.submit(*args, True, broadcast)
    gate.submit(ADDRESSES[0], ADDRESSES[1], b"second", 181, 818, True, broadcast)
    with pytest.raises(ValueError, match="limit"):
        gate.submit(ADDRESSES[2], ADDRESSES[1], b"third", 181, 1000, True, broadcast)
    assert len(calls) == 2
    gate.close()
    changed = policy()
    changed["max_transactions"] = 100
    with pytest.raises(ValueError, match="changed"):
        SpendingGate(path, changed)


def test_uncertain_submission_blocks_all_wallets(tmp_path):
    gate = SpendingGate(tmp_path / "budget.db", policy())

    def failed():
        raise TimeoutError("ambiguous submission")

    with pytest.raises(TimeoutError):
        gate.submit(ADDRESSES[0], ADDRESSES[1], b"first", 181, 1000, True, failed)
    with pytest.raises(ValueError, match="Uncertain"):
        gate.submit(ADDRESSES[2], ADDRESSES[1], b"second", 181, 1000, True, failed)
    gate.close()


@pytest.mark.parametrize(
    "destination,fee,balance,packet",
    [
        ("dero1" + "z" * 61, 181, 1000, b"x"),
        (ADDRESSES[1], 182, 1000, b"x"),
        (ADDRESSES[1], 181, 181, b"x"),
        (ADDRESSES[1], 181, 1000, bytes(79)),
    ],
)
def test_gate_rejects_outside_policy(tmp_path, destination, fee, balance, packet):
    gate = SpendingGate(tmp_path / "budget.db", policy())
    with pytest.raises(ValueError):
        gate.submit(
            ADDRESSES[0],
            destination,
            packet,
            fee,
            balance,
            True,
            lambda: pytest.fail("Must not broadcast"),
        )
    assert gate.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
    gate.close()


@pytest.mark.parametrize("limiting_field", ["max_debit_atomic", "participants"])
def test_cost_and_per_wallet_limits_independently(tmp_path, limiting_field):
    limits = policy()
    limits["max_transactions"] = 10
    if limiting_field == "max_debit_atomic":
        limits["max_debit_atomic"] = 182
    else:
        limits["max_debit_atomic"] = 1820
        limits["participants"][ADDRESSES[0]] = 1
    gate = SpendingGate(tmp_path / "budget.db", limits)
    gate.submit(ADDRESSES[0], ADDRESSES[1], b"first", 181, 1000, True, lambda: "b" * 64)
    with pytest.raises(ValueError, match="limit"):
        gate.submit(
            ADDRESSES[0],
            ADDRESSES[1],
            b"second",
            181,
            818,
            True,
            lambda: pytest.fail("Limit must prevent broadcast"),
        )
    gate.close()
