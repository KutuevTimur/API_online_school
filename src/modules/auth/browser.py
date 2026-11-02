from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from src.modules.auth.depends import get_auth_service, get_token_service
from src.modules.auth.auth_service import AuthService
from src.modules.auth.token_service import TokenService
from src.modules.auth.models_dto import BrowserTokenResponse, TokenResponse, LogoutResponse
from src.modules.auth.exception import InvalidCredentials
from src.modules.account_invitations.rate_limit import check_rate_limit

COOKIE = 'lgg_refresh'


async def browser_guard(request: Request) -> None:
    config = request.app.state.config.browser
    content_type = request.headers.get('content-type', '').split(';')[0].strip().lower()
    allowed = {'application/x-www-form-urlencoded'} if request.url.path.endswith('/login') else {'application/json'}
    if (request.headers.get('origin') != config.origin
            or request.headers.get('x-lgg-request') != 'browser' or content_type not in allowed):
        raise HTTPException(403, 'Browser request rejected')


router = APIRouter(prefix='/auth/browser', tags=['Browser authentication'], dependencies=[Depends(browser_guard)])


async def browser_response(request: Request, response: Response, tokens: TokenResponse, service: TokenService) -> BrowserTokenResponse:
    config = request.app.state.config
    response.headers['Cache-Control'] = 'no-store'
    response.set_cookie(config.browser.cookie_name, tokens.refresh_token, httponly=True, secure=config.browser.secure,
                        samesite='lax', path=config.browser.cookie_path,
                        max_age=await service.browser_cookie_max_age(tokens.refresh_token))
    return BrowserTokenResponse(access_token=tokens.access_token, token_type=tokens.token_type)


@router.post('/login', response_model=BrowserTokenResponse, status_code=200)
async def login(request: Request, response: Response, form: OAuth2PasswordRequestForm = Depends(),
                service: AuthService = Depends(get_auth_service)) -> BrowserTokenResponse:
    await check_rate_limit(request, 'login', form.username)
    tokens = await service.login(form.username, form.password)
    return await browser_response(request, response, tokens, service.token_service)


@router.post('/refresh', response_model=BrowserTokenResponse, status_code=200)
async def refresh(request: Request, response: Response,
                  service: TokenService = Depends(get_token_service)) -> BrowserTokenResponse:
    raw = request.cookies.get(request.app.state.config.browser.cookie_name)
    if not raw:
        raise InvalidCredentials()
    return await browser_response(request, response, await service.refresh_tokens(raw), service)


@router.post('/logout', response_model=LogoutResponse, status_code=200)
async def logout(request: Request, response: Response,
                 service: TokenService = Depends(get_token_service)) -> LogoutResponse:
    await service.refresh_token_service.browser_logout(request.cookies.get(request.app.state.config.browser.cookie_name, ''))
    response.delete_cookie(request.app.state.config.browser.cookie_name, path=request.app.state.config.browser.cookie_path,
                           httponly=True, secure=request.app.state.config.browser.secure, samesite='lax')
    response.headers['Cache-Control'] = 'no-store'
    return LogoutResponse(success=True)
