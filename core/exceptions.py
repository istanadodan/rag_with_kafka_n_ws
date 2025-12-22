class BaseException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DatabaseException(BaseException):
    pass


class CommunicationException(BaseException):
    pass


class ValidationException(BaseException):
    pass


class DomainException(BaseException):
    pass
