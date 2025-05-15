import utils
import tba_communicator as tba
import statbotics_communicator as sb
import pandas as pd
import statbotics
import logging
import statistics
from typing import Any
import datetime
from timer import Timer
import asyncio

log = logging.getLogger("export_tba_sb_data")


class TeamExporter:
    "Holds functions to export team data from TBA and Statbotics"

    sb = statbotics.Statbotics()
    SCHEMA = utils.read_schema("schema/tba_sb_data.yml")
    ALL_EVENT_TYPES = [
        "Preseason",
        "District",
        "Regional",
        "Championship Finals",
        "Championship Division",
        "Offseason",
        "District Championship",
        "District Championship Division",
    ]

    def __init__(
        self,
        teams: list[str],
        year: str,
        excluded_event_types: list[str] = ["Preseason", "Offseason"],
        include_epa: bool = True,
    ):
        "Initialize teams to calculate, competition year, and event types to ignore. Optionally, can exclude EPA from all calculations."
        self.teams = teams
        self.year = year
        self.include_epa = include_epa

        self.event_keys = tba.get_event_keys(teams, year, excluded_event_types)

        self.team_epas = self.get_team_epas(self.teams) if include_epa else None

        self.raw_data = dict()
        self.consolidated_data = dict()

    def get_matches(self, event_key: str) -> list[dict]:
        "Gets all TBA matches from a competition"
        return tba.tba_request(f"event/{event_key}/matches")

    def get_event_keys(self, teams, year, excluded_event_types: list[str]) -> list[str]:
        "Given a list of teams, gets all events where one or more of those teams played"
        log.info("Extracting event keys...")

        all_keys = []

        count = 1
        total = len(teams)

        for team in teams:
            utils.progress_bar(count, total)

            all_keys.extend(
                list(
                    map(
                        lambda e: e["key"],
                        filter(
                            lambda event: event["event_type_string"] not in excluded_event_types,
                            tba.tba_request(f"/team/frc{team}/events/{year}"),
                        ),
                    )
                )
            )

            count += 1

        return list(set(all_keys))

    def export_statbotics(self) -> list[dict]:
        "Returns data from Statbotics as specified in the schema."
        export = []

        for team in self.teams:
            team_data = {"team_number": team}
            for datapoint, requires in self.SCHEMA["--statbotics"].items():
                try:
                    team_data[datapoint] = self.extract_nested_dict(self.team_epas[team], requires)
                except Exception as err:
                    log.error(f"Cannot retrieve datapoint {requires} from statbotics: {err}")
                    team_data[datapoint] = None
            export.append(team_data)

        return export

    def get_raw_data(self, weight_by_epa: bool = False) -> dict[dict[str, Any]]:
        "Extracts raw TIM data for all competitions played by teams in `self.teams`. If `weight_by_epa=True`, estimates the individual team's contribution to each data point by multiplying by their EPA fraction."
        log.info("Extracting data from events...")
        count = 1
        total = len(self.event_keys)

        if weight_by_epa:
            all_teams = []
            for event in self.event_keys:
                all_teams.extend(self.get_team_list(self.get_matches(event)))
            all_teams = set(all_teams).difference(set(self.teams))
            self.team_epas.update(self.get_team_epas(all_teams))

        for event_key in self.event_keys:
            utils.progress_bar(count, total)

            matches = tba.tba_request(f"event/{event_key}/matches")

            for team in set(self.get_team_list(matches)).intersection(set(self.teams)):
                if team not in self.raw_data.keys():
                    self.raw_data[team] = {
                        datapoint: []
                        for datapoint in list(self.SCHEMA["--score_breakdown"].keys())
                        + list(self.SCHEMA["--match_data"].keys())
                    }

            for match in matches:
                teams = self.get_teams_in_match(match)
                for color in ["red", "blue"]:
                    for team in set(teams[color]).intersection(set(self.teams)):
                        layers = self.SCHEMA["--statbotics"]["epa"]
                        try:
                            team_epa_frac = (
                                self.extract_nested_dict(self.team_epas[team], layers)
                                / sum(
                                    [
                                        self.extract_nested_dict(self.team_epas[t], layers)
                                        for t in teams[color]
                                    ]
                                )
                                if weight_by_epa
                                else 1
                            )
                        except Exception as e:
                            log.critical(
                                f"Unable to calculate EPA fraction for alliance {teams[color]}: {e}"
                            )

                        for datapoint, requires in self.SCHEMA["--score_breakdown"].items():
                            if match["comp_level"] in requires["comp_level"]:
                                try:
                                    if requires["calc_type"] == "direct":
                                        self.raw_data[team][datapoint].append(
                                            team_epa_frac
                                            * match["score_breakdown"][color][requires["variable"]]
                                        )
                                    elif requires["calc_type"] == "sum":
                                        self.raw_data[team][datapoint].append(
                                            sum(
                                                [
                                                    team_epa_frac
                                                    * match["score_breakdown"][color][tba_name]
                                                    for tba_name in requires["variable"]
                                                ]
                                            )
                                        )
                                except:
                                    continue
                        for datapoint, requires in self.SCHEMA["--match_data"].items():
                            try:
                                if datapoint == "win_rate":
                                    self.raw_data[team][datapoint].append(
                                        match[requires["variable"]] == color
                                    )
                                elif datapoint == "matches_played":
                                    self.raw_data[team][datapoint].append(match["match_number"])
                                else:
                                    self.raw_data[team][datapoint].append(
                                        match[requires["variable"]]
                                    )
                            except:
                                continue

            count += 1

    def consolidate_data(self) -> None:
        "Consolidates `self.raw_data` into an aggregated team document"
        log.info("Consolidating all data...")
        count = 1
        total = len(self.raw_data)
        combined_schema = self.SCHEMA["--score_breakdown"]
        combined_schema.update(self.SCHEMA["--match_data"])

        for team, stats in self.raw_data.items():
            utils.progress_bar(count, total)

            agg_stats = dict()

            for stat, values in stats.items():
                if (
                    combined_schema[stat]["agg_type"] == "mean"
                    or combined_schema[stat]["agg_type"] == "rate"
                ):
                    agg_stats[stat] = sum(values) / len(values) if len(values) != 0 else None
                elif combined_schema[stat]["agg_type"] == "median":
                    agg_stats[stat] = statistics.median(values) if len(values) > 0 else None
                elif combined_schema[stat]["agg_type"] == "len":
                    agg_stats[stat] = len(values)
                elif combined_schema[stat]["agg_type"] == "sum":
                    agg_stats[stat] = sum(values)
                elif combined_schema[stat]["agg_type"] == "mode":
                    agg_stats[stat] = statistics.mode(values) if len(values) > 0 else None
                elif combined_schema[stat]["agg_type"] == "unique":
                    agg_stats[stat] = list(set(values))
                elif combined_schema[stat]["agg_type"] is None:
                    agg_stats[stat] = values

            if self.include_epa:
                for datapoint, requires in self.SCHEMA["--statbotics"].items():
                    try:
                        agg_stats[datapoint] = self.extract_nested_dict(
                            self.team_epas[team], requires
                        )
                    except:
                        agg_stats[datapoint] = None

            self.consolidated_data[team] = agg_stats

            count += 1


class TBATeamExporter:
    SCHEMA = utils.read_schema("schema/tba_sb_data.yml")
    ALL_EVENT_TYPES = [
        "Preseason",
        "District",
        "Regional",
        "Championship Finals",
        "Championship Division",
        "Offseason",
        "District Championship",
        "District Championship Division",
    ]

    def __init__(
        self,
        teams: list[str],
        year: str,
        excluded_event_types: list[str] = ["Preseason", "Offseason"],
    ):
        "Initialize teams to calculate, competition year, and event types to ignore. Optionally, can exclude EPA from all calculations."
        self.teams = teams
        self.year = year
        self.excluded_event_types = excluded_event_types

    async def extract_data(self, only_latest_event: bool = True):
        data = {
            team: {
                "matches_played": 0,
                "matches_leaved": 0,
                "matches_parked": 0,
                "matches_deep_climbed": 0,
            }
            for team in self.teams
        }

        count = 1
        if only_latest_event:
            log.info(f"Extracting data for {len(self.teams)} teams...")
            for team in self.teams:
                utils.progress_bar(count, len(self.teams))

                data[team]["latest_event"] = tba.get_team_latest_event(team, self.year)
                for match in tba.tba_request(f"event/{data[team]['latest_event']}/matches"):
                    teams_in_match = tba.get_teams_in_match(match)

                    for color in ["red", "blue"]:
                        for num, team_in_match in enumerate(teams_in_match[color]):
                            if team_in_match != team:
                                continue

                            data[team]["matches_played"] += 1
                            data[team]["matches_leaved"] += int(
                                match["score_breakdown"][color][f"autoLineRobot{num + 1}"] == "Yes"
                            )
                            data[team]["matches_parked"] += int(
                                match["score_breakdown"][color][f"endGameRobot{num + 1}"]
                                == "Parked"
                            )
                            data[team]["matches_deep_climbed"] += int(
                                match["score_breakdown"][color][f"endGameRobot{num + 1}"]
                                == "DeepCage"
                            )

                count += 1
        else:
            for event_key in (m := await tba.get_event_keys_async(self.teams, self.year)):
                log.info(f"Extracting data for {event_key=}... ({count}/{len(m)})")

                for match in tba.tba_request(f"event/{event_key}/matches"):
                    teams_in_match = tba.get_teams_in_match(match)

                    for color in ["red", "blue"]:
                        for num, team in enumerate(teams_in_match[color]):
                            if team not in self.teams:
                                continue

                            data[team]["matches_played"] += 1
                            data[team]["matches_leaved"] += int(
                                match["score_breakdown"][color][f"autoLineRobot{num + 1}"] == "Yes"
                            )
                            data[team]["matches_parked"] += int(
                                match["score_breakdown"][color][f"endGameRobot{num + 1}"]
                                == "Parked"
                            )
                            data[team]["matches_deep_climbed"] += int(
                                match["score_breakdown"][color][f"endGameRobot{num + 1}"]
                                == "DeepCage"
                            )

                count += 1

        return utils.melt_data(data, "team_number")

    def write_data(
        self,
        data: list[dict],
        file_path: str = f"data/tba_team_export_{datetime.datetime.today().strftime(r'%Y-%m-%d')}.csv",
    ):
        pd.DataFrame(data).to_csv(file_path, index=False)
        log.info(f"Wrote TBA Team data to {file_path=}")


class TIMExporter:
    SCHEMA = utils.read_schema("schema/tba_sb_data.yml")

    def __init__(self, event_keys: list[str], year: str, include_teams: list = None):
        self.event_keys = event_keys
        self.year = year
        self.include_teams = include_teams
        self.export = []
        self.statbotics_data = dict()

    def get_breakdown_data(self, color: str, match: dict) -> dict:
        data = dict()

        for datapoint, requires in self.SCHEMA["--score_breakdown"].items():
            if match["comp_level"] in requires["comp_level"]:
                try:
                    if datapoint == "total_points_no_foul":
                        data[datapoint] = (
                            match["alliances"][color]["score"]
                            - match["score_breakdown"][color]["foulPoints"]
                        )
                    else:
                        data[datapoint] = match["score_breakdown"][color][requires["variable"]]
                except:
                    data[datapoint] = None
            else:
                data[datapoint] = None

        return data

    def get_statbotics_data(self, raw: dict) -> list[dict]:
        if not raw:
            return None

        data = dict()

        for datapoint, levels in self.SCHEMA["--statbotics"].items():
            data[datapoint] = utils.extract_nested_dict(raw, levels)

        return data

    def export_competition(self, event_key: str, include_epa: bool = True) -> list[dict]:
        comp_export = []
        matches = tba.tba_request(f"event/{event_key}/matches")

        if include_epa:
            self.statbotics_data.update(
                sb.get_team_exports(
                    list(
                        set(tba.get_teams_from_matches(matches)).difference(
                            set(self.statbotics_data.keys())
                        )
                    ),
                    self.year,
                )
            )

        log.info("Extracting TBA data...")
        for match in matches:
            teams = tba.get_teams_in_match(match)
            if self.include_teams and not set(teams["red"] + teams["blue"]).intersection(
                self.include_teams
            ):
                continue

            for color in ["red", "blue"]:
                breakdown = self.get_breakdown_data(color, match)

                for num, team in enumerate(teams[color]):
                    if self.include_teams and team not in self.include_teams:
                        continue
                    try:
                        video_link = f"https://www.youtube.com/watch?v={match['videos'][0]['key']}"
                    except:
                        log.error(
                            f"No video link for match {match['key'].split('_')[-1]} in competition {match['event_key']}."
                        )
                        video_link = None

                    team_export = {
                        "team_number": team,
                        "event_key": match["event_key"],
                        "match_number": match["key"].split("_")[-1],
                        "alliance_color": color,
                        "video_link": video_link,
                        "final_score": match["alliances"][color]["score"],
                        "won_match": match["winning_alliance"] == color,
                    }

                    breakdown["auto_leave"] = (
                        match["score_breakdown"][color][f"autoLineRobot{num + 1}"] == "Yes"
                    )
                    breakdown["endgame_climb"] = match["score_breakdown"][color][
                        f"endGameRobot{num + 1}"
                    ]
                    team_export.update(breakdown)

                    if include_epa:
                        team_sb = self.get_statbotics_data(self.statbotics_data.get(team, None))
                        team_export.update(team_sb)

                    comp_export.append(team_export)
        return comp_export

    def create_export(
        self,
        include_epa: bool = True,
        file_path: str = f"data/tba_sb_tim_export_{datetime.datetime.today().strftime(r'%Y-%m-%d')}.csv",
    ) -> None:
        full_data = []

        timer = Timer()

        count = 1
        for event_key in self.event_keys:
            log.info(f"Exporting {event_key}... ({count}/{len(self.event_keys)})")
            full_data.extend(self.export_competition(event_key, include_epa))
            count += 1

        utils.write_ld_to_file(
            full_data,
            f"data/tba_sb_tim_export_{datetime.datetime.today().strftime(r'%Y-%m-%d')}.csv",
        )
        log.info(f"Export finished, wrote data to {file_path}.")

        timer.end_timer(__file__)


async def main():
    YEAR = "2025"

    calc = "tba_team"

    if calc == "tim":
        # events = tba.get_events_played(YEAR, date_window=["2025-04-04", "9999-12-31"])

        teams = list(set(tba.get_teams_in_event("2025dal")))
        events = await tba.get_event_keys_async(teams, YEAR)

        tim_exporter = TIMExporter(events, YEAR, teams)
        tim_exporter.create_export(True)
    elif calc == "tba_team":
        # teams = tba.get_teams_in_event("2025dal")

        teams = []
        for event in [
            "2025arc",
            "2025cur",
            "2025gal",
            "2025hop",
            "2025dal",
            "2025joh",
            "2025mil",
            "2025new",
            "2025cmptx",
        ]:
            teams.extend(tba.get_teams_in_event(event))
        teams = list(set(teams))

        exporter = TBATeamExporter(teams, YEAR)
        data = await exporter.extract_data()
        exporter.write_data(data)


asyncio.run(main())
