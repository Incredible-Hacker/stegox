"""Engine: orchestrates hide, extract, detect, and analyze operations.

The engine layer is the only layer that knows about all five modules
(image, audio, video, text, metadata). It is also the only layer that
mutates the filesystem — modules and detectors return result objects
that the engine then persists.
"""

from stegox.engine.analyze import analyze
from stegox.engine.detect import detect
from stegox.engine.extract import extract
from stegox.engine.hide import hide
from stegox.engine.pipeline import run_pipeline

__all__ = ["analyze", "detect", "extract", "hide", "run_pipeline"]
