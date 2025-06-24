import asyncio
import logging
from typing import Any, Dict, List

from temporalio import activity

from temporal_worker.models.io_models import (
    DeleteJobPostInput,
    DuplicateJobPostInput,
    GetBoardByNameInput,
    GetExistingJobPostsInput,
    JobPostLocation,
    SetJobPostStatusInput,
)

logger = logging.getLogger(__name__)


class FakeGreenhouseActivities:
    @activity.defn
    async def get_existing_job_posts_by_location(
        self, input_data: GetExistingJobPostsInput
    ) -> List[JobPostLocation]:
        await asyncio.sleep(0.5)

        # create fake existing posts for first N locations
        N = len(input_data.target_locations) // 2
        existing_posts = []
        for i, location in enumerate(input_data.target_locations[:N]):
            existing_posts.append(
                JobPostLocation(id=10000 + i, location=location)
            )

        logger.info(f"Found {len(existing_posts)} existing posts to delete")
        return existing_posts

    @activity.defn
    async def delete_job_post(self, input_data: DeleteJobPostInput) -> bool:
        await asyncio.sleep(0.3)
        logger.info(
            f"Fake deleted job post {input_data.post_id} "
            f"for job {input_data.job_id}"
        )
        return True

    @activity.defn
    async def duplicate_job_post(
        self, input_data: DuplicateJobPostInput
    ) -> Dict[str, Any]:
        await asyncio.sleep(1.0)

        # generate a fake new post ID
        new_post_id = 20000 + hash(input_data.location) % 10000

        result = {
            "job_application_id": new_post_id,
            "location": input_data.location,
            "board_id": input_data.board_id,
            "source_post_id": input_data.source_post_id,
            "status": "draft",
        }

        logger.info(
            f"Fake duplicated post {input_data.source_post_id} to "
            f"{input_data.location} with new ID {new_post_id}"
        )
        return result

    @activity.defn
    async def get_board_by_name(
        self, input_data: GetBoardByNameInput
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.2)

        return {
            "id": 456,
            "name": input_data.board_name,
            "publish_status_id": 789,
            "token": "fake-board-token",
        }

    @activity.defn
    async def set_job_post_status(
        self, input_data: SetJobPostStatusInput
    ) -> bool:
        await asyncio.sleep(0.4)
        logger.info(
            f"Fake set post {input_data.post_id} status to {input_data.status}"
        )
        return True

    @activity.defn
    async def get_target_board_name(self) -> str:
        await asyncio.sleep(0.1)
        return "Fake Target Board"
