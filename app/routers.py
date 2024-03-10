from fastapi import APIRouter, Body
import logging
from app.utilities import handle_github_webhook, process_prompt, test_github, add_comment_to_github_pr

logger = logging.getLogger(__name__)
router = APIRouter()


def get_status():
    """
    Get the status of the service.

    Returns:
        dict: A dictionary containing the service status.
    """
    return {"status": "Service is up and running"}


router.add_api_route("/status/", endpoint=get_status, methods=["GET"])
router.add_api_route("/prompt/", endpoint=process_prompt, methods=["POST"])
router.add_api_route("/webhook/", endpoint=handle_github_webhook, methods=["POST"])

# using this to test github integration from swagger
router.add_api_route("/gh_test/", endpoint=test_github, methods=["GET"])
router.add_api_route("/gh_add_comment/", endpoint=add_comment_to_github_pr, methods=["POST"])
