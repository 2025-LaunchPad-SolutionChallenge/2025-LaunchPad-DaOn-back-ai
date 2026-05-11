from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int, code: int, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message


class BadRequestException(AppException):
    def __init__(self, message: str = "잘못된 요청입니다."):
        super().__init__(status_code=400, code=400, message=message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "인증이 필요합니다."):
        super().__init__(status_code=401, code=401, message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "접근 권한이 없습니다."):
        super().__init__(status_code=403, code=403, message=message)


class NotFoundException(AppException):
    def __init__(self, message: str = "리소스를 찾을 수 없습니다."):
        super().__init__(status_code=404, code=404, message=message)


class ConflictException(AppException):
    def __init__(self, message: str = "이미 존재하는 리소스입니다."):
        super().__init__(status_code=409, code=409, message=message)


class UnprocessableException(AppException):
    def __init__(self, message: str = "처리할 수 없는 요청입니다."):
        super().__init__(status_code=422, code=422, message=message)


class InternalServerException(AppException):
    def __init__(self, message: str = "서버 오류가 발생했습니다."):
        super().__init__(status_code=500, code=500, message=message)
