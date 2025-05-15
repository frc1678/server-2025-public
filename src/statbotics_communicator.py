import statbotics
import requests
import logging
from typing import Union
import utils

log = logging.getLogger("statbotics_communicator")

sb = statbotics.Statbotics()


def statbotics_request(api_url: str, params: dict[str, str] = dict()) -> Union[dict, list]:
    """Sends a single web request to the Statbotics REST API v3."""

    if params:
        params_str = ""
        for param, val in params.items():
            params_str += f"{param}={val}&"

    full_url = (
        f"https://api.statbotics.io/v3/{api_url}?{params_str}"
        if params
        else f"https://api.statbotics.io/v3/{api_url}"
    )

    try:
        request = requests.get(full_url)
    except requests.exceptions.ConnectionError:
        log.error("Error: No internet connection.")
        return None

    return request.json()


def get_team_exports(teams: list[str], year: str) -> dict[str, dict]:
    "Gets the Statbotics export for a list of teams."
    log.info("Extracting EPAs...")

    epas = dict()
    total = len(teams)
    count = 1

    for team in teams:
        utils.progress_bar(count, total)
        epas[team] = sb.get_team_year(int(team), int(year))
        count += 1

    return epas
