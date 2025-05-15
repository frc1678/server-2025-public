import json
import pymongo
import statistics
import server
import utils
import logging

log = logging.getLogger(__name__)


class BaseCalculations:
    # Used for converting to a type that is given as a string
    STR_TYPES = {"str": str, "float": float, "int": int, "bool": bool}

    def __init__(self, server: "server.Server"):
        self.server = server
        self.watched_collections = NotImplemented  # Calculations should override this attribute
        self.teams_list = self.get_teams_list()

    @staticmethod
    def avg(nums, weights=None, default=None):
        """Calculates the average of a list of numeric types.

        If the optional parameter weights is given, calculates a weighted average
        weights should be a list of floats. The length of weights must be the same as the length of nums
        default is the value returned if nums is an empty list
        """
        if len(nums) == 0:
            return default
        if weights is None:
            # Normal (not weighted) average
            return sum(nums) / len(nums)
        if len(nums) != len(weights):
            raise ValueError(f"Weighted average expects one weight for each number.")
        weighted_sum = sum([num * weight for num, weight in zip(nums, weights)])
        return weighted_sum / sum(weights)

    @staticmethod
    def modes(data: list) -> list:
        """Returns the most frequently occurring items in the given list"""
        if len(data) == 0:
            return []
        # Create a dictionary of things to how many times they occur in the list
        frequencies = {}
        for item in data:
            frequencies[item] = 1 + frequencies.get(item, 0)
        # How many times each mode occurs in nums:
        max_occurrences = max(frequencies.values())
        return [item for item, frequency in frequencies.items() if frequency == max_occurrences]

    @staticmethod
    def get_z_scores(nums: list) -> list:
        """Given a list of numbers, returns their Z-scores"""
        standard_deviation = statistics.pstdev(nums)
        mean = BaseCalculations.avg(nums)
        if standard_deviation == 0:
            return [num - mean for num in nums]
        return [(num - mean) / standard_deviation for num in nums]

    @staticmethod
    def get_teams_list():
        try:
            with open(f"data/{utils.TBA_EVENT_KEY}_team_list.json") as file:
                reader = json.load(file)

                return reader
        except FileNotFoundError:
            log.error(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json not found")
            return []

    @staticmethod
    def get_aim_list():
        """match_schedule.json is a dictionary with keys as match numbers and values of lists of team dicts.

        Each team dict contains alliance color and team number.
        Returns a list of dictionaries of aims with match_number, alliance_color, and team_list data.
        """
        try:
            with open(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json") as file:
                reader = json.load(file)
        except FileNotFoundError:
            log.error(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json not found")
            return []
        aim_list = []
        for match in reader:
            for alliance in ["blue", "red"]:
                aim = {"match_number": int(match), "alliance_color": alliance[0].upper()}
                aim["team_list"] = [
                    team["number"] for team in reader[match]["teams"] if alliance == team["color"]
                ]
                aim_list.append(aim)
        return aim_list
