import logging
import time

logger = logging.getLogger('django.request')

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if response.status_code >= 400:
            logger.warning(
                f"{request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"User: {request.user} - "
                f"Time: {duration:.2f}s"
            )
        
        return response

    def process_exception(self, request, exception):
        logger.error(
            f"Исключение в {request.method} {request.path}: {exception}",
            exc_info=True,
            extra={'request': request}
        )
        return None