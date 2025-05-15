import json
import export_csvs
import utils
import logging
import os

log = logging.getLogger(__name__)


# If no data in predicted_aim, ends
def find_prediction_metrics(predicted_aim_data):

    if len(predicted_aim_data) == 0:
        log.error("No data in predicted_aim")
        return


# Calculation functions ================================================================


# Calculates the square-root of the mean squared error between all of the match phase's predicted and actual scores
def calc_rmse(predicted_aim_data):
    for phase in ["_auto", "_tele", "_endgame", ""]:
        total = 0
        for aim in predicted_aim_data:
            actual = aim["actual_score" + phase]
            predicted = aim["predicted_score" + phase]
            total += (actual - predicted) ** 2
        rmse = (total / len(predicted_aim_data)) ** (1 / 2)


# Calculates the win_chance_accuracy by counting the number of correct predictions and averaging them
def calc_win_chance_accuracy(predicted_aim_data):
    correct_predictions = 0
    for aim in predicted_aim_data:
        if round(aim["win_chance"]) == aim["won_match"]:
            correct_predictions += 1
    win_chance_accuracy = correct_predictions / len(predicted_aim_data)

    return win_chance_accuracy


calculation_functions = {"win_chance_accuracy": calc_win_chance_accuracy, "rmse": calc_rmse}


def calc_prediction_metrics(predicted_aim_data):
    schema = utils.read_schema("schema/calc_predicted_aim_schema.yml")
    original_json = {"by_match_statistics": []}
    phase = ["_auto", "_tele", "_endgame", ""]

    # Stores the data of each team's performance in predictions_summary.json
    for aim in predicted_aim_data:
        entry = {}
        for key, value in aim.items():
            entry[key] = value

        for phase in schema:
            actual = "actual_score" + phase
            predicted = "predicted_score" + phase
            if actual in aim:
                entry[actual] = aim[actual]
            if predicted in aim:
                entry[predicted] = aim[predicted]

        original_json["by_match_statistics"].append(entry)
        original_json["overall_match_statistics"] = {
            name: func(predicted_aim_data) for name, func in calculation_functions.items()
        }

    return original_json


# Reads the event key and creates a json file that includes the name of the competition, by match statistics, and overall match statistics
if __name__ == "__main__":
    # Prompts user to read from cloud
    read_cloud = (
        True if utils.input("Read from cloud database? (y/N): ").lower() in ["y", "yes"] else False
    )
    utils.confirm_comp(f"You are working with competition {utils.server_key()}, and {read_cloud=}.")

    exporter = export_csvs.BaseExport()
    data = exporter.get_data(["predicted_aim"], read_cloud)["predicted_aim"]

    with open(f"data/{utils.server_key()}_predictions_summary.json", "w") as f:
        json.dump(calc_prediction_metrics(data), f, indent=4)
