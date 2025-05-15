import json
import statistics
import utils
import summarize_predictions
from export_csvs import BaseExport
import os


class SummarizeCompetition:
    def __init__(self, cloud):
        self.cloud = cloud

    def get_avg_stat(self, collection, datapoint):
        exporter = BaseExport()
        data = exporter.load_single_collection(collection, self.cloud)
        return statistics.mean([entry[datapoint] for entry in data if datapoint in entry.keys()])

    def get_prediction_metrics(self):
        exporter = BaseExport()
        aim_data = exporter.load_single_collection("predicted_aim", self.cloud)
        return summarize_predictions.calc_prediction_metrics(aim_data)

    def write_to_json(self):
        # avg_name: [collection_name, datapoint_name]
        variables_to_collect = {
            "avg_spr": ["sim_precision", "sim_precision"],
            "avg_pickability": ["pickability", "first_pickability"],
        }
        summary_data = {
            key: self.get_avg_stat(data[0], data[1]) for key, data in variables_to_collect.items()
        }
        summary_data["prediction_metrics"] = self.get_prediction_metrics()
        with open(f"data/{utils.server_key()}_summary.json", "w") as json_file:
            json.dump(summary_data, json_file, indent=4)


if __name__ == "__main__":
    cloud = True if utils.input("Use cloud or local data? ").lower() in ["cloud", "c"] else False

    utils.confirm_comp(f"You are working with competition {utils.server_key()}, and {cloud=}.")

    summarize_competition = SummarizeCompetition(cloud)
    summarize_competition.write_to_json()
