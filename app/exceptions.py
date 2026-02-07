from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Base exception for authentication errors."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenError(AuthenticationError):
    """Exception raised when token is invalid or expired."""

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(detail=detail)


class UserNotFoundError(HTTPException):
    """Exception raised when user is not found."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class UserAlreadyExistsError(HTTPException):
    """Exception raised when user already exists."""

    def __init__(self, detail: str = "User already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class RateLimitExceededError(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class LeagueNotFoundError(HTTPException):
    """Exception raised when league is not found."""

    def __init__(self, detail: str = "League not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class NotLeagueMemberError(HTTPException):
    """Exception raised when user is not a member of the league."""

    def __init__(self, detail: str = "You are not a member of this league"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class MatchAlreadyStartedError(HTTPException):
    """Exception raised when trying to modify prediction for a match that has started."""

    def __init__(self, detail: str = "This match has already started"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class AlreadyLeagueMemberError(HTTPException):
    """Exception raised when user is already a member of the league."""

    def __init__(self, detail: str = "You are already a member of this league"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class MatchNotFoundError(HTTPException):
    """Exception raised when match is not found."""

    def __init__(self, detail: str = "Match not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ForbiddenError(HTTPException):
    """Exception raised when user lacks permission."""

    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class InsufficientFundsError(HTTPException):
    """Exception raised when user has insufficient balance for bet."""

    def __init__(self, detail: str = "Insufficient balance"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class InvalidInputError(HTTPException):
    """Exception raised for invalid input."""

    def __init__(self, detail: str = "Invalid input"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class BetNotFoundError(HTTPException):
    """Exception raised when bet is not found."""

    def __init__(self, detail: str = "Bet not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
