"""Shared fixtures over the real sample files in data/samples (never modified)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sevcon_diff.application.compare_service import CompareDcfFiles
from sevcon_diff.application.diff_engine import DcfDiffEngine
from sevcon_diff.domain.models import DcfDocument
from sevcon_diff.infrastructure.dcf_parser import SevconDcfReader
from sevcon_diff.infrastructure.rule_classifier import TomlNoiseFilter, TomlRuleClassifier

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"
CIRCE = SAMPLES / "circe-MS2223.dcf"
CIRCE_V8 = SAMPLES / "DCF_10_04-v8_Circe_FuncionaPresentacion.dcf"
PRIMER = SAMPLES / "Primer_mapa_fk1.dcf"
MOTORLAND = SAMPLES / "Motorland_Carrera1_100_30.dcf"
MOTORLAND_RACE2 = SAMPLES / "Motorland_Carrera2_100..150_30.dcf"
MOTORLAND_QUALY = SAMPLES / "Motorland_Qualy1_120_40.dcf"
MOTORLAND_V7 = SAMPLES / "Motorland_v7_45kW.dcf"
MOTORLAND_V2 = SAMPLES / "Motorland_v2_MapaCambiado.dcf"
MOTORLAND_V3 = SAMPLES / "Motorland_v3_MapaCambiado_encoder_reinsaw_Ajustado.dcf"
MOTORLAND_V4 = SAMPLES / "Motorland_v4_UMA.dcf"
SEGUNDO = SAMPLES / "Segundo_mapa_fk1_Temperatura.dcf"
DOS_MAPAS = SAMPLES / "2MapasLimitadosPara30-06_PunoRespuestaRapida.dcf"
ALL_SAMPLES = (
    CIRCE, CIRCE_V8, PRIMER, SEGUNDO, DOS_MAPAS, MOTORLAND, MOTORLAND_RACE2, MOTORLAND_QUALY,
    MOTORLAND_V2, MOTORLAND_V3, MOTORLAND_V4, MOTORLAND_V7,
)


@pytest.fixture(scope="session")
def reader() -> SevconDcfReader:
    return SevconDcfReader()


@pytest.fixture(scope="session")
def circe_doc(reader: SevconDcfReader) -> DcfDocument:
    return reader.read(CIRCE)


@pytest.fixture(scope="session")
def classifier() -> TomlRuleClassifier:
    return TomlRuleClassifier()


@pytest.fixture(scope="session")
def noise_filter() -> TomlNoiseFilter:
    return TomlNoiseFilter()


@pytest.fixture(scope="session")
def engine(classifier: TomlRuleClassifier, noise_filter: TomlNoiseFilter) -> DcfDiffEngine:
    return DcfDiffEngine(classifier, noise_filter)


@pytest.fixture(scope="session")
def compare(reader: SevconDcfReader, engine: DcfDiffEngine) -> CompareDcfFiles:
    return CompareDcfFiles(reader, engine)
