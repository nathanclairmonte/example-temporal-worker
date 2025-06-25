import asyncio
import logging
import uuid
from datetime import datetime

from temporalio.client import Client

from temporal_worker.config import read_config
from temporal_worker.init_logging import init_logging
from temporal_worker.models.io_models import (
    ReplicateJobPostsInput,
    ReplicateJobPostsOutput,
)

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

    # create dummy input data
    timestamp_id = (
        f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_{uuid.uuid4().hex[:8]}"
    )
    workflow_id = f"example-workflow-{timestamp_id}"
    workflow_input = ReplicateJobPostsInput(
        source_post_id=11111,
        regions=["americas"],
        job_id=22222,
        user_email="nathan.clairmonte@canonical.com",
    )

    logger.info(
        f"Starting fake replicate workflow with workflow ID: {workflow_id}"
    )

    # start the workflow
    try:
        result = await client.execute_workflow(
            "FakeReplicateJobPostsWorkflow",
            workflow_input,
            id=workflow_id,
            task_queue="example-workflow-queue",
        )

        result = ReplicateJobPostsOutput(**result)
        logger.info("Fake workflow completed successfully!")
        logger.info(f"Workflow tyoe: {result.workflow_type}")
        logger.info(f"Success: {result.success}")
        logger.info(f"Created posts: {len(result.created_posts)}")
        logger.info(f"Deleted posts: {len(result.deleted_posts)}")
        logger.info(f"Errors: {len(result.errors)}")

        if result.errors:
            logger.warning(f"Workflow had errors: {result.errors}")

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
