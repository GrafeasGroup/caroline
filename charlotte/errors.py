class UserError(Exception):
    def __init__(self, message, *args):
        self.message = message  # bypass DeprecationWarning
        super().__init__(message, *args)


class CharlotteConnectionError(Exception):
    def __init__(self, message, *args):
        self.message = message  # bypass DeprecationWarning
        super().__init__(message, *args)
