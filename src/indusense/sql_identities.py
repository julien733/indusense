from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, String, cast, create_engine, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Float, Integer, Numeric


@dataclass(frozen=True)
class IdentityResult:
    source: Path
    artifact: Path
    tables: int
    rows: int
    columns: int


@dataclass(frozen=True)
class ColumnIdentity:
    table: str
    name: str
    inferred_type: str
    minimum: Any = None
    maximum: Any = None
    mean: Any = None
    median: Any = None


def detect_charset(path: Path) -> tuple[str, str]:
    """Retourne le libelle du charset et le codec Python correspondant."""
    content = path.read_bytes()
    if content.startswith(b"\xef\xbb\xbf"):
        return "UTF-8 BOM", "utf-8-sig"

    for label, codec in (
        ("UTF-8", "utf-8"),
        ("Windows-1252", "cp1252"),
        ("ISO-8859-1", "iso-8859-1"),
    ):
        try:
            content.decode(codec)
            return label, codec
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Impossible de determiner le charset de {path}")


def human_size(byte_count: int) -> str:
    units = ("o", "Ko", "Mo", "Go", "To")
    size = float(byte_count)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    raise AssertionError("Unite de taille inaccessible")


def _sqlite_compatible_sql(sql: str) -> str:
    """Adapte les constructions PostgreSQL presentes dans les dumps fournis."""
    sql = re.sub(r"\bTIMESTAMPTZ\b", "TIMESTAMP", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bNOW\s*\(\s*\)", "CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)
    return sql


def _load_dump(source: Path, encoding: str) -> Engine:
    sql = source.read_text(encoding=encoding)
    if not sql.strip():
        raise ValueError("Le fichier SQL est vide.")

    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        raw_connection = engine.raw_connection()
        try:
            raw_connection.executescript(_sqlite_compatible_sql(sql))
            raw_connection.commit()
        finally:
            raw_connection.close()
    except Exception:
        engine.dispose()
        raise
    return engine


def _infer_type(column: Any) -> str:
    name = column.name.casefold()
    if column.primary_key or column.foreign_keys or name == "id" or name.endswith("_id"):
        return "IDENTITY"
    if isinstance(column.type, Boolean):
        return "BOOLEAN"
    if isinstance(column.type, DateTime):
        return "DATETIME"
    if isinstance(column.type, Date):
        return "DATE"
    if isinstance(column.type, (Integer, Numeric, Float)):
        return "NUMERIC"
    return "TEXT"


def _column_identity(connection: Any, table: Any, column: Any) -> ColumnIdentity:
    inferred_type = _infer_type(column)
    base = {"table": table.name, "name": column.name, "inferred_type": inferred_type}

    if inferred_type == "NUMERIC":
        values = list(connection.scalars(select(column).where(column.is_not(None))))
        if values:
            return ColumnIdentity(
                **base,
                minimum=min(values),
                maximum=max(values),
                mean=statistics.fmean(values),
                median=statistics.median(values),
            )
    elif inferred_type in {"DATE", "DATETIME"}:
        # Le cast evite les differences de conversion entre dialectes pour MIN/MAX.
        minimum, maximum = connection.execute(
            select(func.min(cast(column, String)), func.max(cast(column, String)))
        ).one()
        if minimum is not None:
            return ColumnIdentity(**base, minimum=minimum, maximum=maximum)

    return ColumnIdentity(**base)


def _inspect_database(engine: Engine) -> tuple[list[tuple[str, int, int]], list[ColumnIdentity]]:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    if not metadata.tables:
        raise ValueError("Aucune table n'a ete trouvee dans le fichier SQL.")

    table_summaries: list[tuple[str, int, int]] = []
    columns: list[ColumnIdentity] = []
    with engine.connect() as connection:
        for table_name in inspect(engine).get_table_names():
            table = metadata.tables[table_name]
            row_count = connection.scalar(select(func.count()).select_from(table)) or 0
            table_summaries.append((table_name, row_count, len(table.columns)))
            columns.extend(
                _column_identity(connection, table, column) for column in table.columns
            )
    return table_summaries, columns


def _markdown_escape(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ")


def _display(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (datetime, date, time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _artifact_name(source: Path, started_at: datetime) -> str:
    basename = source.name[: -len(".sql.txt")]
    return f"{basename}_{started_at.strftime('%H%M%S')}.md"


def make_sql_identity(source: Path, output_root: Path) -> IdentityResult:
    started_at = datetime.now().astimezone()
    charset_label, encoding = detect_charset(source)
    engine = _load_dump(source, encoding)
    try:
        tables, columns = _inspect_database(engine)
    finally:
        engine.dispose()

    ended_at = datetime.now().astimezone()
    rows_number = sum(row_count for _, row_count, _ in tables)
    cols_number = sum(column_count for _, _, column_count in tables)
    day_directory = output_root / started_at.strftime("%Y%m%d")
    day_directory.mkdir(parents=True, exist_ok=True)
    artifact = day_directory / _artifact_name(source, started_at)

    lines = [
        f"* Source: {source.resolve()}",
        f"* Filsize: {human_size(source.stat().st_size)}",
        f"* ProcessBeginAt: {started_at.strftime('%H:%M:%S')}",
        f"* ProcessEndAt: {ended_at.strftime('%H:%M:%S')}",
        f"* Charset: {charset_label}",
        f"* Rows Number: {rows_number}",
        f"* Cols Number: {cols_number}",
        f"* Tables Number: {len(tables)}",
        "",
        "## Tables",
        "",
        "| Table | Rows Number | Cols Number |",
        "| --- | ---: | ---: |",
    ]
    lines.extend(f"| {_markdown_escape(name)} | {rows} | {cols} |" for name, rows, cols in tables)
    lines.extend(
        [
            "",
            "## Column list",
            "",
            "| Table | Colname | Infered Type |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(
        f"| {_markdown_escape(item.table)} | {_markdown_escape(item.name)} | {item.inferred_type} |"
        for item in columns
    )
    lines.extend(
        [
            "",
            "## Numeric and temporal statistics",
            "",
            "| Table | Col name | Infered Type | Min value | Max value | Mean value | Median value |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    statistical_columns = [
        item for item in columns if item.inferred_type in {"NUMERIC", "DATE", "DATETIME"}
    ]
    if statistical_columns:
        lines.extend(
            "| "
            + " | ".join(
                _markdown_escape(_display(value))
                for value in (
                    item.table,
                    item.name,
                    item.inferred_type,
                    item.minimum,
                    item.maximum,
                    item.mean,
                    item.median,
                )
            )
            + " |"
            for item in statistical_columns
        )
    else:
        lines.append("| _Aucune colonne numerique ou temporelle_ | N/A | N/A | N/A | N/A | N/A | N/A |")

    artifact.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return IdentityResult(
        source=source.resolve(),
        artifact=artifact.resolve(),
        tables=len(tables),
        rows=rows_number,
        columns=cols_number,
    )


def generate_sql_identities(
    input_directory: Path = Path("datas"),
    output_root: Path = Path("artifacts/ingestion/identities"),
) -> list[IdentityResult]:
    sources = sorted(input_directory.glob("*.sql.txt"))
    if not sources:
        raise FileNotFoundError(
            f"Aucun fichier .sql.txt trouve dans {input_directory.resolve()}"
        )

    results: list[IdentityResult] = []
    for source in sources:
        try:
            results.append(make_sql_identity(source, output_root))
        except Exception as exc:
            print(f"ERREUR pendant le traitement de {source.resolve()}")
            print(f"{type(exc).__name__}: {exc}")
            raise RuntimeError(f"Traitement interrompu sur {source.name}") from exc

    print(f"Traitement termine avec succes : {len(results)} fichier(s) traite(s).")
    for result in results:
        print(
            f"- {result.source.name}: {result.tables} table(s), "
            f"{result.rows} ligne(s), {result.columns} colonne(s) -> {result.artifact}"
        )
    return results


if __name__ == "__main__":
    generate_sql_identities()
