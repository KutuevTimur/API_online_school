"""Shared external meeting URL validation; never fetch the address."""
from typing import Annotated
from pydantic import AfterValidator, HttpUrl, TypeAdapter

_http_url = TypeAdapter(HttpUrl)


def validate_call_url(value: str) -> str:
    return str(_http_url.validate_python(value))


CallURL = Annotated[str, AfterValidator(validate_call_url)]
