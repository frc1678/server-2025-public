from export_csvs import BaseExport

exporter = BaseExport()
data = exporter.get_data(["obj_team", "pickability"], False)

import json


def get_team_data(file_path, team_number):
    """Fetches team data and specific pickability data from the specified JSON file."""
    try:
        with open(file_path) as f:
            data = json.load(f)

        obj_team = data.get("obj_team", [])
        team_data = next(
            (team for team in obj_team if str(team.get("team_number")) == team_number), None
        )

        pickability = data.get("pickability", [])
        pickability_data = next(
            (team for team in pickability if str(team.get("team_number")) == team_number), {}
        )
        filtered_pickability = {
            "first_pickability": pickability_data.get("first_pickability", "N/A"),
            "defense_proxy_second_pickability": pickability_data.get(
                "defense_proxy_second_pickability", "N/A"
            ),
        }

        return team_data, filtered_pickability
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' contains invalid JSON.")
        return None, None


team_number = input("Enter the number of the team: ").strip()

if team_number:
    file_path = "data/data.json"
    team_data, pickability_data = get_team_data(file_path, team_number)

    if team_data:
        expected_cycle_time = (
            round(team_data.get("avg_expected_cycle_time", 0), 2)
            if isinstance(team_data.get("avg_expected_cycle_time"), (int, float))
            else "N/A"
        )
        avg_total_points = (
            round(team_data.get("avg_total_points", 0), 2)
            if isinstance(team_data.get("avg_total_points"), (int, float))
            else "N/A"
        )
        auto_avg_total_points = (
            round(team_data.get("auto_avg_total_points", 0), 2)
            if isinstance(team_data.get("auto_avg_total_points"), (int, float))
            else "N/A"
        )
        endgame_avg_total_points = (
            round(team_data.get("endgame_avg_total_points", 0), 2)
            if isinstance(team_data.get("endgame_avg_total_points"), (int, float))
            else "N/A"
        )
        tele_avg_total_points = (
            round(team_data.get("tele_avg_total_points", 0), 2)
            if isinstance(team_data.get("tele_avg_total_points"), (int, float))
            else "N/A"
        )

        first_pickability = (
            round(pickability_data["first_pickability"], 2)
            if isinstance(pickability_data["first_pickability"], (int, float))
            else "N/A"
        )
        defense_proxy_second_pickability = (
            round(pickability_data["defense_proxy_second_pickability"], 2)
            if isinstance(pickability_data["defense_proxy_second_pickability"], (int, float))
            else "N/A"
        )

        print(f"\nTeam {team_number} Data:")
        print("Pickability:")
        print(f"  First Pickability: {first_pickability}")
        print(f"  Defense Proxy Second Pickability: {defense_proxy_second_pickability}")
        print(f"Expected Cycle Time: {expected_cycle_time}")
        print(f"Average Total Points: {avg_total_points}")
        print(f"Average Auto Points: {auto_avg_total_points}")
        print(f"Average Endgame Points: {endgame_avg_total_points}")
        print(f"Teleop Average Total Points: {tele_avg_total_points}")
    else:
        print(f"Team {team_number} Not Found.")
else:
    print("Invalid input. Please enter a valid team number.")
