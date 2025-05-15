"""Puts all pit images for the competition into data/{event_key}_pit_images/"""

import kestrel_communicator as kc
import utils
import os
from logging import getLogger

log = getLogger(__name__)

if __name__ == "__main__":
    if not os.path.exists(f"data/{utils.server_key()}_pit_images"):
        os.mkdir(f"data/{utils.server_key()}_pit_images")
    pit_image_list = kc.kestrel_request(f"database/pit_collection/image_list/{utils.server_key()}")
    num_images = 0
    for image in pit_image_list:
        utils.progress_bar(num_images + 1, len(pit_image_list))
        # pit_image_list will be a list of file names
        # Get the image from the database
        response = kc.kestrel_request(
            f"database/pit_collection/images/{utils.server_key()}/{image}", json=False
        )
        open(f"data/{utils.server_key()}_pit_images/{image}", "wb").write(response.content)
        log.info(f"Downloaded {image}")
        num_images += 1
    log.info(f"Downloaded {num_images} pit images")
