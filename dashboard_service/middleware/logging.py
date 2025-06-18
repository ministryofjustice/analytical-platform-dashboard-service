import uuid

import structlog


class LoggingContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        For each request, generate a unique request ID and bind it to the logger.
        This allows us to trace logs related to a specific request.
        Also binds the user's email if available, or marks it as anonymous.
        """
        rid = uuid.uuid4().hex
        structlog.get_logger().bind(
            request_id=rid, user=request.user.email if request.user.is_authenticated else "<anon>"
        )
        response = self.get_response(request)
        return response
