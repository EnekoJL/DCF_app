"""Compare two DCF documents by ObjectKey using decoded values."""

from __future__ import annotations

from sevcon_diff.application.value_decoder import ValueDecoder, format_signed
from sevcon_diff.domain.diff_models import (
    ChangeKind,
    DecodedValue,
    DiffResult,
    DiffSummary,
    FileSummary,
    ParameterChange,
)
from sevcon_diff.domain.models import DataType, DcfDocument, DcfParameter, ObjectKey
from sevcon_diff.domain.ports import NoiseFilter, ParameterClassifier


class DcfDiffEngine:
    """Builds a :class:`DiffResult`: union of keys, decoded comparison, classification."""

    def __init__(
        self,
        classifier: ParameterClassifier,
        noise_filter: NoiseFilter,
        decoder: ValueDecoder | None = None,
    ) -> None:
        self._classifier = classifier
        self._noise = noise_filter
        self._decoder = decoder or ValueDecoder()

    def diff(self, doc_a: DcfDocument, doc_b: DcfDocument) -> DiffResult:
        keys = sorted(set(doc_a.parameters) | set(doc_b.parameters), key=lambda k: k.sort_key)
        changes: list[ParameterChange] = []
        for key in keys:
            change = self._compare(doc_a.get(key), doc_b.get(key))
            if change is not None:
                changes.append(change)
        result_changes = tuple(changes)
        return DiffResult(
            file_a=FileSummary.from_document(doc_a, self._checksum(doc_a)),
            file_b=FileSummary.from_document(doc_b, self._checksum(doc_b)),
            changes=result_changes,
            summary=DiffSummary.from_changes(result_changes),
            groups=self._classifier.groups(),
        )

    def _checksum(self, doc: DcfDocument) -> str | None:
        key: ObjectKey | None = self._noise.checksum_key
        param = doc.get(key) if key is not None else None
        if param is None:
            return None
        decoded = self._decoder.decode(param)
        return decoded.raw_hex or decoded.display

    def _compare(
        self, old: DcfParameter | None, new: DcfParameter | None
    ) -> ParameterChange | None:
        old_value = self._decoder.decode(old) if old is not None else None
        new_value = self._decoder.decode(new) if new is not None else None
        if old is not None and new is not None:
            assert old_value is not None and new_value is not None
            if old_value.identity == new_value.identity:
                return None
            kind = ChangeKind.MODIFIED
        else:
            kind = ChangeKind.ADDED if old is None else ChangeKind.REMOVED
        reference = new if new is not None else old
        assert reference is not None
        return self._build_change(kind, reference, old_value, new_value)

    def _build_change(
        self,
        kind: ChangeKind,
        param: DcfParameter,
        old: DecodedValue | None,
        new: DecodedValue | None,
    ) -> ParameterChange:
        meta = param.metadata
        low = self._decoder.decode_literal(param.low_limit, param) if param.low_limit else None
        high = self._decoder.decode_literal(param.high_limit, param) if param.high_limit else None
        default = (
            self._decoder.decode_literal(param.default_value, param)
            if param.default_value
            else None
        )
        delta, delta_percent = self._delta(param, old, new)
        data_type = param.data_type_enum
        return ParameterChange(
            key=param.key,
            kind=kind,
            name=param.name,
            parent_name=param.parent_name,
            group=self._classifier.classify(param),
            old=old,
            new=new,
            units=meta.units,
            is_noise=(reason := self._noise.noise_reason(param)) is not None,
            noise_reason=reason,
            delta=delta,
            delta_percent=delta_percent,
            delta_display=format_signed(delta) if delta is not None else "",
            bit_changes=self._decoder.bit_changes(param, old, new),
            description=meta.description,
            category=meta.category,
            data_type=param.data_type,
            data_type_name=data_type.name if data_type else str(param.data_type or ""),
            access_type=param.access_type,
            access_level=meta.access_level,
            write_in_preop_only=meta.write_in_preop_only,
            low_limit=low,
            high_limit=high,
            default=default,
            old_out_of_limits=_out_of_limits(old, low, high),
            new_out_of_limits=_out_of_limits(new, low, high),
        )

    def _delta(
        self, param: DcfParameter, old: DecodedValue | None, new: DecodedValue | None
    ) -> tuple[float | None, float | None]:
        """Numeric delta, only for quantities (not flags, enums or bit fields)."""
        meta = param.metadata
        if (
            old is None
            or new is None
            or old.enum_label
            or new.enum_label
            or meta.enum
            or meta.is_bit_split
            or meta.is_hex_format
            or param.data_type_enum is DataType.BOOLEAN
        ):
            return None, None
        old_num = self._decoder.numeric(old)
        new_num = self._decoder.numeric(new)
        if old_num is None or new_num is None:
            return None, None
        delta = new_num - old_num
        percent = delta / abs(old_num) * 100.0 if old_num else None
        return delta, percent


def _out_of_limits(
    value: DecodedValue | None, low: DecodedValue | None, high: DecodedValue | None
) -> bool:
    if value is None or value.integer is None:
        return False
    low_int = low.integer if low is not None else None
    high_int = high.integer if high is not None else None
    if low_int is not None and high_int is not None and low_int > high_int:
        return False  # inconsistent limits in the file (e.g. 0xFFFF on a signed type)
    if low_int is not None and value.integer < low_int:
        return True
    return high_int is not None and value.integer > high_int

