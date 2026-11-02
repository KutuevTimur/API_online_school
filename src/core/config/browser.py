from urllib.parse import urlsplit
from pydantic import BaseModel


class BrowserConfig(BaseModel):
    origin: str
    secure: bool
    cookie_path: str = '/api/auth/browser'
    cookie_name: str = 'lgg_refresh'

    @classmethod
    def build(cls, values: dict[str, str], mode: str) -> 'BrowserConfig':
        local = mode in {'DEV', 'TEST'}
        origin = values.get('BROWSER_ORIGIN', 'http://127.0.0.1:5173' if local else '')
        secure = values.get('BROWSER_COOKIE_SECURE', '0' if local else '1') == '1'
        parsed = urlsplit(origin)
        if (not origin or parsed.scheme not in {'http', 'https'} or not parsed.netloc
                or parsed.path or parsed.query or parsed.fragment or parsed.username
                or (not local and (not secure or parsed.scheme != 'https'))):
            raise RuntimeError('Invalid browser origin/cookie configuration')
        return cls(origin=origin, secure=secure)
