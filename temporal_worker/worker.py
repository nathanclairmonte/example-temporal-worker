import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from temporal_worker.activities.activities import FakeGreenhouseActivities
from temporal_worker.config import read_config
from temporal_worker.init_logging import init_logging
from temporal_worker.workflows.workflow import FakeReplicateJobPostsWorkflow

logger = logging.getLogger(__name__)


async def main():
    init_logging()
    config = read_config()
    if not config["temporal"]["server_url"]:
        raise Exception("Missing Temporal server URL in environment variables")

    # connect to Temporal server
    logger.info("Connecting to Temporal server...")
    client = await Client.connect(
        config["temporal"]["server_url"], namespace="default"
    )

    # create worker
    fake_greenhouse_activities = FakeGreenhouseActivities()
    worker = Worker(
        client,
        task_queue="example-workflow-queue",
        workflows=[
            FakeReplicateJobPostsWorkflow,
        ],
        activities=[
            fake_greenhouse_activities.get_existing_job_posts_by_location,
            fake_greenhouse_activities.delete_job_post,
            fake_greenhouse_activities.duplicate_job_post,
            fake_greenhouse_activities.get_board_by_name,
            fake_greenhouse_activities.set_job_post_status,
            fake_greenhouse_activities.get_target_board_name,
        ],
    )

    logger.info("Starting Temporal worker...")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
