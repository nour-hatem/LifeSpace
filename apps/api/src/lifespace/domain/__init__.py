"""Pure business rules for LifeSpace.

The domain layer holds the application's business rules as plain Python: it imports
only the standard library and other ``lifespace.domain`` modules, performs no I/O,
and never reads the clock or generates identifiers. Values such as the current
instant, ids, and the user's ``ZoneInfo`` are always passed in by the caller
(ADR 0001 item 14).
"""
