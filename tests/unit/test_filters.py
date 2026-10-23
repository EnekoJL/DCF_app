from __future__ import annotations

from fakes import MOTOR, OTHER

from sevcon_diff.application.filters import DiffQuery
from sevcon_diff.domain.diff_models import ChangeKind, ParameterChange
from sevcon_diff.domain.models import ObjectKey


def change(
    key: str, name: str, *, motor: bool = False, noise: bool = False, parent: str | None = None,
    description: str = "",
) -> ParameterChange:
    return ParameterChange(
        key=ObjectKey.parse(key),
        kind=ChangeKind.MODIFIED,
        name=name,
        parent_name=parent,
        group=MOTOR if motor else OTHER,
        old=None,
        new=None,
        is_noise=noise,
        description=description,
    )


CHANGES = (
    change("4641sub5", "Number of Pole Pairs", motor=True, parent="AC Motor data"),
    change("4651sub1", "Speed proportional gain", motor=True, description="Uses 4.12 scaling"),
    change("29A0sub1", "Trip", noise=True),
    change("1800sub2", "Transmission type", parent="Transmit PDO"),
)


def keys(query: DiffQuery) -> list[str]:
    return [c.key.section for c in query.apply(CHANGES)]


def test_default_hides_noise() -> None:
    assert keys(DiffQuery()) == ["4641sub5", "4651sub1", "1800sub2"]


def test_show_noise() -> None:
    assert "29A0sub1" in keys(DiffQuery(show_noise=True))


def test_motor_only() -> None:
    assert keys(DiffQuery(motor_only=True)) == ["4641sub5", "4651sub1"]


def test_group_ids() -> None:
    assert keys(DiffQuery(group_ids=frozenset({"other"}))) == ["1800sub2"]
    assert keys(DiffQuery(group_ids=frozenset())) == []


def test_text_search_over_key_name_parent_description() -> None:
    assert keys(DiffQuery(text="4641sub5")) == ["4641sub5"]
    assert keys(DiffQuery(text="0x4641.05")) == ["4641sub5"]
    assert keys(DiffQuery(text="4641h")) == ["4641sub5"]
    assert keys(DiffQuery(text="POLE pairs")) == ["4641sub5"]
    assert keys(DiffQuery(text="ac motor")) == ["4641sub5"]
    assert keys(DiffQuery(text="4.12 scaling")) == ["4651sub1"]
    assert keys(DiffQuery(text="trip")) == []
    assert keys(DiffQuery(text="trip", show_noise=True)) == ["29A0sub1"]
    assert keys(DiffQuery(text="   ")) == ["4641sub5", "4651sub1", "1800sub2"]
