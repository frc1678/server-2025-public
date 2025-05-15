import trueskill as ts
import tba_communicator as tba
import utils
import json
from typing import Union
import datetime
import global_team_stats as gts


def update_ratings(red_teams: list[str], blue_teams: list[str], red_won: bool) -> None:
    "Update ratings of teams after one match"
    new_ratings = env.rate(
        [
            tuple([ratings[team] for team in red_teams]),
            tuple([ratings[team] for team in blue_teams]),
        ],
        [0, 1] if red_won else [1, 0],
    )

    updated_dict = {red_teams[i]: new_ratings[0][i] for i in range(3)}
    updated_dict.update({blue_teams[i]: new_ratings[1][i] for i in range(3)})

    for team, rating in updated_dict.items():
        ratings[team] = rating


def play_matches(matches: list[dict]) -> None:
    "Plays a list of TBA matches and updates ratings of teams"
    for match in matches:
        teams = gts.get_teams_in_match(match)
        update_ratings(teams["red"], teams["blue"], match["winning_alliance"] == "red")


def play_competitions(
    event_keys: list,
    event_types: list = [
        "Preseason",
        "District",
        "Regional",
        "Championship Finals",
        "Championship Division",
        "Offseason",
        "District Championship",
        "District Championship Division",
    ],
) -> None:
    "Plays the specified competitions and updates ratings of teams"
    print("Playing competitions...")

    sorted_event_keys = list(
        map(
            lambda event: event["key"],
            filter(
                lambda event: event["key"] in event_keys
                and event["event_type_string"] in event_types,
                sorted(
                    tba.tba_request(f"events/2024"),
                    key=lambda event: datetime.datetime.strptime(event["end_date"], r"%Y-%m-%d"),
                ),
            ),
        )
    )

    count = 1
    total = len(sorted_event_keys)
    for event_key in sorted_event_keys:
        utils.progress_bar(count, total)

        matches = tba.tba_request(f"event/{event_key}/matches")

        for team in gts.get_team_list(matches):
            if team not in ratings.keys():
                ratings[team] = env.create_rating()

        play_matches(matches)

        count += 1


def get_viewable_ratings(only_mu=False) -> dict[str, list]:
    "Gets a viewable version of the TrueSkill ratings to display"
    viewable = dict()

    for team, rating in ratings.items():
        viewable[team] = [rating.mu, rating.sigma] if not only_mu else rating.mu

    return viewable


def display_leaderboard(filepath: Union[str, None], n: int = 100) -> None:
    "Writes viewable TrueSkill ratings to the specified filepath"
    viewable = dict(
        sorted(
            {team: val[0] - 2 * val[1] for team, val in get_viewable_ratings().items()}.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    count = 1
    if filepath is not None:
        with open(filepath, "w") as f:
            for team, rating in viewable.items():
                if count <= n:
                    f.writelines(f"({count}) {team}: {round(rating, 1)}\n")
                    count += 1
                else:
                    break
    else:
        for team, rating in viewable.items():
            if count <= n:
                print(f"({count}) {team}: {round(rating[0], 1)}, {round(rating[1], 1)}")
                count += 1
            else:
                break


if __name__ == "__main__":
    env = ts.TrueSkill(draw_probability=0)

    ratings = dict()
    team_stats = dict()
    year = "2024"

    competitions = list(map(lambda event: event["key"], tba.tba_request(f"events/{year}")))

    play_competitions(competitions, ["Regional"])

    display_leaderboard("data/leaderboard.txt", 100)
