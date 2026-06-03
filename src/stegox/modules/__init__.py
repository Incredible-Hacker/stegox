"""StegoX modules: per-medium embed and extract implementations."""

from stegox.modules.audio import embed_audio, extract_audio
from stegox.modules.audio import list_strategies as audio_strategies
from stegox.modules.image import embed_image, extract_image
from stegox.modules.image import list_strategies as image_strategies
from stegox.modules.metadata import embed_metadata, extract_metadata
from stegox.modules.metadata import list_fields as metadata_fields
from stegox.modules.text import embed_text, extract_text
from stegox.modules.text import list_strategies as text_strategies
from stegox.modules.video import embed_video, extract_video
from stegox.modules.video import list_strategies as video_strategies

__all__ = [
    "audio_strategies",
    "embed_audio",
    "embed_image",
    "embed_metadata",
    "embed_text",
    "embed_video",
    "extract_audio",
    "extract_image",
    "extract_metadata",
    "extract_text",
    "extract_video",
    "image_strategies",
    "metadata_fields",
    "text_strategies",
    "video_strategies",
]
