class ConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        cookie = request.get_signed_cookie("validator_connected", False)
        request.connected = 0
        if cookie == "connected":
            request.connected = 1
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
