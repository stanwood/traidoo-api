from rest_framework.permissions import IsAuthenticated


class GetPermissionsMixin:
    permission_classes_by_action = {"default": [IsAuthenticated]}

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [
                permission()
                for permission in self.permission_classes_by_action["default"]
            ]
