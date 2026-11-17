import traceback
from dataclasses import dataclass, asdict
from types import TracebackType
from typing import List, Optional, Dict, Any


@dataclass
class StackFrameDto:
    filename: str
    line_number: int
    function_name: str
    code_line: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExceptionDto:
    error_type: str
    message: str
    frames: List[StackFrameDto]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "frames": [frame.to_dict() for frame in self.frames],
        }


def normalize_exception(
    exc_type: Optional[type],
    exc_value: Optional[BaseException],
    exc_tb: Optional[TracebackType],
) -> ExceptionDto:
    error_type_name = exc_type.__name__ if exc_type is not None else type(exc_value).__name__
    error_message = str(exc_value) if exc_value is not None else ""

    frames: List[StackFrameDto] = []
    if exc_tb is not None:
        extracted = traceback.extract_tb(exc_tb)
        for frame in extracted:
            frames.append(
                StackFrameDto(
                    filename=frame.filename,
                    line_number=frame.lineno or 0,
                    function_name=frame.name,
                    code_line=frame.line or "",
                )
            )

    return ExceptionDto(
        error_type=error_type_name,
        message=error_message,
        frames=frames,
    )