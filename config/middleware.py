import logging
import time
import traceback

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """Middleware для логирования HTTP запросов с кодом >= 400"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if response.status_code >= 400:
            logger.warning(
                "%s %s - Status: %d - User: %s - Time: %.2fs",
                request.method,
                request.path,
                response.status_code,
                request.user,
                duration,
            )
        
        return response


class ErrorLoggingMiddleware:
    """Middleware для перехвата и логирования всех необработанных исключений"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as exc:
            logger = logging.getLogger('django.request')
            logger.error(
                "Unhandled exception in %s %s: %s",
                request.method,
                request.path,
                str(exc),
                exc_info=True,
                extra={
                    'request': request,
                    'stack': traceback.format_exc(),
                }
            )
            raise
        return response