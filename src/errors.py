from werkzeug.exceptions import HTTPException


class FileUploadError(HTTPException):
    """Base class for all file-related errors, defaults to 400"""

    code = 400
    description = "A general error occurred during file upload."


class MissingUploadFileError(FileUploadError):
    """Missing Upload File Error"""

    code = 400
    description = "No file was uploaded."


class InvalidMediaFormatError(FileUploadError):
    """Unsupported Media Type File Error"""

    code = 415
    description = "Only PNG and JPG files are supported."


class MissingCollectorParam(HTTPException):
    """Missing Collector Parameter Error"""

    code = 400
    description = "Missing required collector parameter."
