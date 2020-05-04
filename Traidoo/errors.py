class AppError(Exception):
    """ Root exception for all application exceptions."""
    ERROR_CODE = 'APPLICATION_ERROR'


class AppConfigurationError(AppError):
    ERROR_CODE = 'APPLICATION_CONFIGURATION_ERROR'


# Datastore errors
class DatastoreError(AppError):
    """ Root exception for all database errors"""
    ERROR_CODE = 'DATASTORE_ERROR'


class EntityExistError(DatastoreError):
    ERROR_CODE = 'ENTITY_EXIST'


class MissingRequiredPropertyError(DatastoreError):
    ERROR_CODE = 'MISSING_REQUIRED_PROPERTY'


class InvalidDataError(DatastoreError):
    ERROR_CODE = 'INVALID_DATA'


class EntityNotFound(DatastoreError):
    ERROR_CODE = "ENTITY_NOT_FOUND"


class ConstraintError(DatastoreError):
    ERROR_CODE = "DATA_CONSTRAINT_ERROR"


class DataConsistencyError(DatastoreError):
    ERROR_CODE = "DATA_CONSISTENCY_ERROR"


# Request errors
class RequestError(AppError):
    """ Base error for all incorrect requests except security related."""
    ERROR_CODE = "INCORRECT_REQUEST"
    code = 400


class IncorrectPayloadError(RequestError):
    ERROR_CODE = "INCORRECT_PAYLOAD"
    code = 400


class IncorrectQueryStringError(RequestError):
    ERROR_CODE = "INCORRECT_QUERY_STRING"


class TemporaryError(RequestError):
    """ User should be instructed to retry and report issue if it persist. """
    ERROR_CODE = 'TEMPORARY_ERROR'


# Authentication and authorization errors
class AuthError(AppError):
    """ This exception should not be used, but errors which inherit form it."""
    ERROR_CODE = "AUTH_ERROR"


class LoginRequiredError(AuthError):
    ERROR_CODE = "LOGIN_REQUIRED"
    code = 401


class IncorrectCredentialsError(AuthError):
    ERROR_CODE = "INCORRECT_CREDENTIALS"
    code = 401


class UserArchivedError(AuthError):
    ERROR_CODE = "USER_ARCHIVED"


class AccessDeniedError(AuthError):
    ERROR_CODE = "ACCESS_DENIED"
    code = 401


class IncorrectSessionTokenError(AuthError):
    ERROR_CODE = "INCORRECT_SESSION_TOKEN"
    code = 401


class PermissionsSetupError(AuthError):
    """ Permission configuration error on app side """
    ERROR_CODE = "PERMISSIONS_SETUP_ERROR"


class IncorrectEmailValidationToken(AuthError):
    ERROR_CODE = "INCORRECT_EMAIL_VALIDATION_TOKEN"
    code = 404

class PaymentError(AppError):
    ERROR_CODE = 'PAYMENT_ERROR'
