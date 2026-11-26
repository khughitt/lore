"""The one exception every user-facing failure of context selection raises."""


class ContextError(Exception):
    """A selection input, context or command argument lore refuses."""
