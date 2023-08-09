import asyncio
import io
import logging
import logging.config
from pathlib import Path
from typing import Literal, Optional

import click

from covsurver_client.client import fetch_covsurver_report

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "%(asctime)s - %(message)s"}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "covsurver-client": {
                "handlers": ["stdout"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
    }
)

logger = logging.getLogger("covsurver-client")


@click.command()
@click.argument("fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", help="Output filename")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["tsv", "csv", "xlsx"]),
    default="tsv",
    show_default=True,
    help="Output format",
)
def cli(
    fasta: Path,
    output: Optional[str] = None,
    format: Literal["tsv", "csv", "xlsx"] = "tsv",
) -> None:
    """Fetch CovSurver report for a fasta file. Saves raw tsv output by default."""

    logger.info("Fasta file: %s", fasta.resolve())

    with open(fasta, "r") as fi:
        report = asyncio.run(fetch_covsurver_report(fi))

    if report is None:
        click.echo("Got no data.")
        return

    if output is None:
        output_path = fasta.with_suffix(f".{format}")
    else:
        output_path = Path(output)

    if format == "tsv":
        with open(output_path, "w") as fo:
            fo.write(report)
    else:
        import pandas as pd

        stream = io.StringIO(report)
        df = pd.read_csv(stream, sep="\t", dtype="string")  # type: ignore
        if format == "csv":
            df.to_csv(output_path, index=False)
        elif format == "xlsx":
            df.to_excel(output_path, index=False)  # type: ignore

    logger.info("Output file: %s", output_path.resolve())


if __name__ == "__main__":
    cli()
