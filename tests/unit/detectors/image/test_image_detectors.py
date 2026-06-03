"""Image detector tests."""

from __future__ import annotations

import pytest

from stegox.core.types import DetectionContext
from stegox.detectors.image.chi_square import ChiSquareDetector
from stegox.detectors.image.histogram import HistogramDetector
from stegox.detectors.image.lsb_distribution import LsbDistributionDetector
from stegox.detectors.image.rs_analysis import RSAnalysisDetector
from stegox.modules.image import embed_lsb


def _ctx(path) -> DetectionContext:
    from stegox.core.constants import MediaType
    from stegox.utils.hashing import hash_file

    h = hash_file(path)
    return DetectionContext(
        target_path=path,
        hashes=h,
        media_type=MediaType.IMAGE,
        format_name="png",
    )


def test_lsb_distribution_flags_embedded(sample_png, tmp_path) -> None:
    out = tmp_path / "stego.png"
    embed_lsb(sample_png, out, b"\x00" * 100)
    det = LsbDistributionDetector()
    result = det.run(_ctx(out))
    assert 0.0 <= result.score <= 1.0
    assert result.indicators


def test_chi_square_runs(sample_png) -> None:
    det = ChiSquareDetector()
    result = det.run(_ctx(sample_png))
    assert 0.0 <= result.score <= 1.0


def test_rs_analysis_runs(sample_png) -> None:
    det = RSAnalysisDetector()
    result = det.run(_ctx(sample_png))
    assert 0.0 <= result.score <= 1.0


def test_histogram_runs(sample_png) -> None:
    det = HistogramDetector()
    result = det.run(_ctx(sample_png))
    assert 0.0 <= result.score <= 1.0
