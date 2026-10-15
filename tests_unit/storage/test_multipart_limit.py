import httpx
import pytest
from fastapi import FastAPI, File, UploadFile
from src.modules.storage.middleware import MultipartBodyLimitMiddleware


@pytest.mark.asyncio
async def test_missing_or_lying_content_length_does_not_bypass_stream_limit():
    app=FastAPI()
    app.add_middleware(MultipartBodyLimitMiddleware,max_bytes=1024)
    @app.post('/upload')
    async def upload(file: UploadFile=File(...)):
        return {'size':len(await file.read())}
    body=(b'--test\r\nContent-Disposition: form-data; name="file"; filename="x.pdf"\r\n'
          b'Content-Type: application/pdf\r\n\r\n'+b'x'*1500+b'\r\n--test--\r\n')
    async def chunks():
        for start in range(0,len(body),200):yield body[start:start+200]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        for length in [None,'1','2000']:
            headers={'Content-Type':'multipart/form-data; boundary=test'}
            if length:headers['Content-Length']=length
            response=await client.post('/upload',content=chunks(),headers=headers)
            assert response.status_code==413,response.text
