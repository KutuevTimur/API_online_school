import pytest
from src.core.config.browser import BrowserConfig

@pytest.mark.parametrize('values', [{}, {'BROWSER_ORIGIN': 'http://school.example'}, {'BROWSER_ORIGIN': 'https://school.example', 'BROWSER_COOKIE_SECURE': '0'}, {'BROWSER_ORIGIN': 'https://school.example/'}, {'BROWSER_ORIGIN': 'null'}])
def test_production_fails_closed(values):
    with pytest.raises(RuntimeError):
        BrowserConfig.build(values, 'PRODUCTION')

def test_production_secure():
    conf = BrowserConfig.build({'BROWSER_ORIGIN': 'https://school.example'}, 'PRODUCTION')
    assert conf.secure and conf.cookie_path == '/api/auth/browser'
