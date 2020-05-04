import datetime
import json

from django.conf import settings
from django.utils import timezone
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2


class TasksMixin:
    @property
    def _cloud_tasks_client(self):
        return tasks_v2.CloudTasksClient()

    def send_task(
        self,
        url,
        queue_name="default",
        http_method="POST",
        payload=None,
        schedule_time=None,
        headers=None
    ):
        parent = self._cloud_tasks_client.queue_path(
            settings.GOOGLE_CLOUD_PROJECT,
            settings.GOOGLE_CLOUD_PROJECT_LOCATION,
            queue_name,
        )

        task = {
            "app_engine_http_request": {
                "http_method": http_method,
                "relative_uri": url
            }
        }

        if headers:
            task["app_engine_http_request"]["headers"] = headers

        if isinstance(payload, dict):
            payload = json.dumps(payload)

        if payload is not None:
            converted_payload = payload.encode()

            task["app_engine_http_request"]["body"] = converted_payload

        if schedule_time is not None:
            # Convert "seconds from now" into an rfc3339 datetime string.
            d = timezone.now() + datetime.timedelta(seconds=schedule_time)

            # Create Timestamp protobuf.
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(d)  # pylint: disable=maybe-no-member

            # Add the timestamp to the tasks.
            task["schedule_time"] = timestamp

        self._cloud_tasks_client.create_task(parent, task)
