from clean_tablets import clean_tablets_function
from send_device_jsons import SendDeviceJSONS
from send_apk import send_apk_function
from unittest.mock import patch
import utils
import os
import tba_communicator

if __name__ == "__main__":
    # Prompt user
    utils.confirm_comp()

    if not os.path.isfile(f"data/{utils.TBA_EVENT_KEY}_team_list.json"):
        tba_communicator.create_team_list(utils.TBA_EVENT_KEY)
    if not os.path.isfile(f"data/{utils.TBA_EVENT_KEY}_match_schedule.json"):
        tba_communicator.create_match_schedule(utils.TBA_EVENT_KEY)

    with patch("builtins.input", return_value="y"):
        clean_tablets_function()
    send_jsons = SendDeviceJSONS()
    send_jsons.send_device_jsons_function()
    with patch("builtins.input", return_value="t"):
        send_apk_function()
