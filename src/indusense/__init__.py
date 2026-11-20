from __future__ import annotations

__all__ = ["main"]


def main() -> None:
    """Point d'entree de la commande ``indusense``."""
    from .sql_identities import generate_sql_identities

    generate_sql_identities()
