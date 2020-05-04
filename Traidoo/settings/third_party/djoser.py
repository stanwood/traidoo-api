DJOSER = {
    "PASSWORD_RESET_CONFIRM_URL": "password/reset/{uid}/{token}",
    "ACTIVATION_URL": "registration/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": False,
    "SERIALIZERS": {
        "user": "users.serializers.UserSerializer",
        "activation": "users.serializers.ActivationSerializer",
        "user_create": "users.serializers.UserCreateSerializer",
    },
    "PERMISSIONS": {"user": ["core.permissions.current_user.CurrentUserOrAdmin"]},
}
