import io
import logging
import re
from typing import Optional, TextIO

import aiohttp

logger = logging.getLogger("covsurver-client")

COVSURVER_BASE_LINK = "https://mendel3.bii.a-star.edu.sg/METHODS/corona/delta6"
COVSURVER_REQUEST_LINK = COVSURVER_BASE_LINK + "/cgi-bin/coronamapBlastAnno.pl"


async def fetch_covsurver_report(fasta: str | TextIO) -> Optional[str]:
    """Fetch CovSurver report for a given fasta. Raw result contains tsv as string.

    Parameters
    ----------
    fasta : str | TextIO
        fasta with sequences

    Returns
    -------
    Optional[str]
        CovSurver report as tsv string
    """

    stream = io.StringIO(fasta) if isinstance(fasta, str) else fasta

    async with aiohttp.ClientSession() as session:
        logger.debug("POST request to: %s", COVSURVER_REQUEST_LINK)

        async with session.post(
            COVSURVER_REQUEST_LINK, data={"seqfile": stream}
        ) as response:
            response_text = await response.text()
            if not response.ok:
                logger.error(
                    "POST response status: %s, body: %s",
                    response.status,
                    response_text,
                )
                return
            else:
                logger.debug("POST response status: %s", response.status)

            result_link_search = re.search(
                r"/mendeltemp/covsurver_result\d+_perquery.tsv", response_text
            )
            if not result_link_search:
                logger.error(
                    "No result link in response, response body: %s", response_text
                )
                return

        result_link = COVSURVER_BASE_LINK + result_link_search.group(0)

        logger.debug("GET request to: %s", result_link)
        async with session.get(result_link) as response:
            if not response.ok:
                logger.error("GET response status: %s", response.status)
                return
            else:
                logger.debug("GET response status: %s", response.status)

            covsurver_report = await response.text()

    return covsurver_report
