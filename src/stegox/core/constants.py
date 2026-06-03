"""Stable string enumerations shared across the codebase."""

from __future__ import annotations

from enum import StrEnum


class MediaType(StrEnum):
    """Coarse-grained media categories used for command dispatch."""

    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    METADATA = "metadata"
    UNIVERSAL = "universal"


class RiskClass(StrEnum):
    """Verdict bands produced by the scoring engine."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Strategy(StrEnum):
    """Stable strategy identifiers for embedders and extractors."""

    # Image
    LSB = "lsb"
    LSB_RGB = "lsb-rgb"
    RANDOMIZED_LSB = "randomized-lsb"
    PASSWORD_EMBED = "password-embed"
    DCT_JPEG = "dct-jpeg"
    # Audio
    PCM_LSB = "pcm-lsb"
    PCM_LSB_RAND = "pcm-lsb-rand"
    ECHO_HIDING = "echo-hiding"
    PHASE_CODING = "phase-coding"
    SPREAD_SPECTRUM = "spread-spectrum"
    # Video
    FRAME_LSB = "frame-lsb"
    FRAME_LSB_RAND = "frame-lsb-rand"
    MOTION_REGION = "motion-region"
    KEYFRAME_DCT = "keyframe-dct"
    # Text
    ZERO_WIDTH = "zero-width"
    WHITESPACE = "whitespace"
    HOMOGLYPH = "homoglyph"
    HOMOGLYPH_ADVANCED = "homoglyph-advanced"


__all__ = ["MediaType", "RiskClass", "Strategy"]
