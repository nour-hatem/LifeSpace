"""Use cases and the ports they need (ADR 0002 items 1 and 2).

The application layer imports only the standard library and ``lifespace.domain``.
It never reads the clock and never generates identifiers: the current instant
and every new id are supplied through the ``Clock`` and ``IdGenerator`` ports
defined in ``lifespace.application.ports`` (ADR 0002 item 1).
"""
