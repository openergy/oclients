class ClientResponseError(Exception):
    def __init__(self, message="Client error", code=None, request=None):
        self.message = message
        self.code = code
        self.request = request

    def __str__(self):
        return f"Error code: {self.code}.\nContent:\n\n{self.message}" + \
               (f"\n\nRequest: {self.request}" if self.request is not None else "")
