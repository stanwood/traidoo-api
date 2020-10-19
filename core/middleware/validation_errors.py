from loguru import logger


def validation_errors_middleware(get_response):
    def middleware(request):
        response = get_response(request)

        if response.status_code == 400:
            logger.debug(response.data)

        return response

    return middleware
