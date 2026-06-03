"""Per-format adapter modules.

Each submodule wraps a specific codec or container and exposes a
``read`` and (where supported) ``write`` function. Modules here are
intentionally thin; logic lives in :mod:`stegox.modules`.
"""
