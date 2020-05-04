from django.urls import path

from .crons.jobs_notifications import JobsNotificationsView
from .tasks.create_job import CreateJobView
from .tasks.create_detours import CreateDetoursView
from .tasks.update_detours import UpdateDetoursView


urlpatterns = [
    path(r'jobs/create/<int:order_item_id>', CreateJobView.as_view()),
    path(r'jobs/cron/notifications/<int:user_id>', JobsNotificationsView.as_view()),
    path(r'jobs/cron/notifications', JobsNotificationsView.as_view()),
    path(r'detours/create/<int:route_id>', CreateDetoursView.as_view()),
    path(r'detours/update/<int:route_id>', UpdateDetoursView.as_view()),
]
