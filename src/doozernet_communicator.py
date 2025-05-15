import requests
import logging
import utils

log = logging.getLogger(__name__)

PREDICTION_PERCENT_CUTOFF = (
    0.8  # must have a percentage higher than this to be considered sufficiently trained
)
DOOZER_SIGIL = open("data/api_keys/doozernet_key.txt").read().strip()
# API docs can be found at https://api.1678doozer.net/docs#


def dn_request(api_url: str, params=None, json=None, type="GET"):
    """Makes a request to the DoozerNet API"""
    base_url = "https://api.1678doozer.net/"
    if type == "GET":
        response = requests.get(
            f"{base_url}{api_url}", params=params, headers={"DoozerSigil": DOOZER_SIGIL}
        )
    elif type == "POST":
        response = requests.post(
            f"{base_url}{api_url}", params=params, json=json, headers={"DoozerSigil": DOOZER_SIGIL}
        )
    response_json = response.json()
    return response_json


def predict(matches: list, use_super=False) -> list:
    """
    Given (theoretical or real) matches of six teams each, return the model's predictions.
    Each match should be a list of team numbers. Red alliance is the first three, blue alliance is the last three
    Returns a list of floats, each representing the confidence in the BLUE alliance.
    """
    matches_ = {}
    for i in range(len(matches)):
        matches_[str(i)] = matches[i]
    tba_key = utils.TBA_EVENT_KEY
    if use_super:
        return dn_request(
            f"prophet/SuperProphet/batch_predict", json={"matches": matches_}, type="POST"
        )
    else:
        return dn_request(
            f"prophet/{tba_key}/batch_predict", json={"matches": matches_}, type="POST"
        )


def predict_matches(match_numbers: list, use_super=False) -> list:
    """
    Given a list of match numbers, return the model's predictions for each match.
    Returns a list of floats, each representing the confidence in the BLUE alliance.
    """
    tba_key = utils.TBA_EVENT_KEY
    return dn_request(
        f"prophet/{tba_key}/batch_predict_matches",
        params={"use_super_prophet": use_super},
        json=match_numbers,
        type="POST",
    )


def check_model_availability() -> str:
    """
    Uses the API to check if the AI model is available.
    If the specific competition model for this competition is NOT sufficiently trained, use the most recent SuperProphet model instead
    If no model is available, return 'None'
    Otherwise, return either 'specific' or 'super' depending on which is available
    """
    try:
        breakdown_specific = dn_request(f"prophet/{utils.TBA_EVENT_KEY}/model_breakdown")
        breakdown_super = dn_request(f"prophet/SuperProphet/model_breakdown")
    except:
        return None
    if breakdown_specific["correct_prediction_percent"] > PREDICTION_PERCENT_CUTOFF:
        return "specific"
    if breakdown_super["correct_prediction_percent"] > PREDICTION_PERCENT_CUTOFF:
        return "super"
    return None
