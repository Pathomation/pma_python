import asyncio

import requests
import json
from typing import List, Optional, IO, Iterable
from urllib.parse import urljoin, quote
from typing import Callable
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager


UploadProgressCallback = Callable[[int, int], None]

class TLS12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
            **pool_kwargs
        )

class _ProgressStream:
    def __init__(self, raw, total_bytes: int, callback: UploadProgressCallback | None):
        self.raw = raw
        self.total_bytes = total_bytes
        self.callback = callback
        self.sent = 0

    def read(self, size=-1):
        chunk = self.raw.read(size)
        if not chunk:
            return chunk
        self.sent += len(chunk)
        if self.callback:
            self.callback(self.sent, self.total_bytes)
        return chunk

    def seek(self, *a, **kw):
        return self.raw.seek(*a, **kw)

    def tell(self):
        return self.raw.tell()


# Model classes
class UploadFileModel:
    def __init__(self, path: str, length: int, isMain: bool):
        """
        :param path: Relative path for the file to upload
        :param length: Length of this file in bytes
        :param isMain: Indicates whether this file is the main file for the slide
        """
        self.path = path
        self.length = length
        self.isMain = isMain

class UploadHeaderModel:
    def __init__(self, path: str, files: Optional[List[UploadFileModel]] = None):
        self.path = path
        self.files = files if files is not None else []

class UploadResponse:
    class UploadTypeEnum:
        FILE_SYSTEM = "FileSystem"
        AMAZON_S3 = "AmazonS3"
        AZURE = "Azure"

    def __init__(self, Id: int, UploadType: Optional[str] = None,
                 Urls: Optional[Iterable[str]] = None,
                 MultipartFiles: Optional[Iterable[dict]] = None):
        self.id = Id
        self.upload_type = UploadType
        self.urls = list(Urls) if Urls is not None else []

        self.multipart_files: List[MultipartFile] = []
        if MultipartFiles:
            for mf in MultipartFiles:
                parts_objs = []
                for p in (mf.get("Parts") or []):
                    parts_objs.append(MultipartFilePart(
                        PartNumber=p["PartNumber"],
                        Url=p["Url"],
                        RangeStart=p["RangeStart"],
                        RangeEnd=p["RangeEnd"],
                    ))
                self.multipart_files.append(MultipartFile(
                    FilePath=mf["FilePath"],
                    UploadId=mf["UploadId"],
                    Parts=parts_objs
                ))

class MultipartFile:
    def __init__(
        self,
        FilePath: str,
        UploadId: str,
        Parts: Optional[Iterable['MultipartFilePart']] = None
    ):
        self.file_path = FilePath
        self.upload_id = UploadId
        self.parts = list(Parts) if Parts is not None else []

class MultipartFilePart:
    def __init__(self, PartNumber: int, Url: str, RangeStart: int, RangeEnd: int):
        self.PartNumber = PartNumber
        self.Url = Url
        self.RangeStart = RangeStart
        self.RangeEnd = RangeEnd

class MultipartUploadHeaderModel:
    def __init__(
        self,
        FilePath: str,
        UploadId: str,
        Parts: Optional[List['PartETagModel']] = None
    ):
        """
        :param FilePath: File path where the uploaded file will be saved.
        :param UploadId: Unique identifier for the multipart upload.
        :param Parts: List of part ETags for the uploaded parts.
        """
        self.file_path = FilePath
        self.upload_id = UploadId
        self.parts = Parts if Parts is not None else []

class PartETagModel:
    def __init__(self, PartNumber: int, ETag: str):
        """
        :param PartNumber: Part number of the uploaded part.
        :param ETag: ETag for the uploaded part, which is a unique identifier.
        """
        self.PartNumber = PartNumber
        self.ETag = ETag

class AuthenticateResponse:
    def __init__(
        self,
        Username: str,
        Success: bool,
        SessionId: str,
        Status: int,
        Reason: str,
        Email: str,
        FirstName: str,
        LastName: str
    ):
        self.username = Username
        self.success = Success
        self.session_id = SessionId
        self.status = Status
        self.reason = Reason
        self.email = Email
        self.first_name = FirstName
        self.last_name = LastName

# Aliases for convenience
MultipartFile = MultipartFile
PartETagModel = PartETagModel
UploadFileModel = UploadFileModel


class PmaCoreClient:
    def __init__(self, pma_core_url: str):
        self.server_url = pma_core_url
        if not self.server_url.lower().startswith(('http://', 'https://')):
            self.server_url = 'http://' + self.server_url
        if not self.server_url.endswith('/'):
            self.server_url += '/'

        self.session = requests.Session()
        self.session.trust_env = False
        self.session.mount("https://", TLS12HttpAdapter())

    def authenticate(self, username: str, password: str, caller: str) -> AuthenticateResponse:
        service_url = urljoin(self.server_url, 'api/json/Authenticate')
        params = {'username': username, 'password': password, 'caller': caller}
        response = requests.get(service_url, params=params)
        response.raise_for_status()
        return self._parse_json(response.text, AuthenticateResponse)

    async def upload_header(self, upload_model: UploadHeaderModel, session_id: str) -> UploadResponse:
        url = urljoin(self.server_url, 'transfer/Upload')
        headers = {'Content-Type': 'application/json'}
        params = {'sessionId': session_id}
        data = json.dumps(upload_model, default=lambda o: o.__dict__)
        response = await asyncio.to_thread(
            requests.post,
            url,
            params=params,
            headers=headers,
            data=data
        )
        response.raise_for_status()
        return UploadResponse(**response.json())

    async def upload_file(self, upload_id: int, upload_type: Optional[str], upload_url: str,
                          relative_path: str, stream: IO, session_id: str,
                          total_bytes: int | None = None,
                          progress_callback: UploadProgressCallback | None = None):

        if upload_type == "Azure" or upload_type == 2:
            await self.upload_file_to_azure(
                upload_url,
                stream,
                total_bytes=total_bytes,
                progress_callback=progress_callback,
            )
            return

        upload_to_presigned = bool(upload_url)

        wrapped = stream
        if progress_callback and total_bytes:
            wrapped = _ProgressStream(stream, total_bytes, progress_callback)

        if upload_to_presigned:
            data = wrapped.read()
            print("========== DEBUG PRESIGNED ==========")
            print("upload_url RAW =", upload_url)
            print("type(upload_url) =", type(upload_url))
            print("====================================")

            headers = {
                "Content-Length": str(len(data))
            }

            import urllib3

            http = urllib3.PoolManager()

            response = await asyncio.to_thread(
                http.request,
                "PUT",
                upload_url,
                body=data,
                headers=headers,
                preload_content=False
            )

            if response.status >= 300:
                raise Exception(f"S3 upload failed: {response.status}")

            return

        url = f"{self.server_url}transfer/Upload/{upload_id}"
        params = {"sessionId": session_id, "path": relative_path}

        files = {"file": (relative_path.split("/")[-1], wrapped, "application/octet-stream")}
        response = await asyncio.to_thread(
            requests.post,
            url,
            params=params,
            files=files
        )
        response.raise_for_status()

    async def get_upload_status(self, id: int, session_id: str) -> str:
        service_url = f"{self.server_url}transfer/Upload/{id}"
        params = {'sessionId': session_id}
        response = await asyncio.to_thread(
            requests.get,
            service_url,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

    async def upload_multipart_file_to_s3(self, multipart_info: MultipartFile, relative_path: str,
                                          stream: IO, session_id: str,
                                          progress_callback: UploadProgressCallback | None = None):
        e_tags = await self.upload_parts_to_s3(
            multipart_info,
            stream,
            progress_callback=progress_callback
        )
        url = f"{self.server_url}transfer/Upload/CompleteMultipart"
        params = {'sessionId': session_id}
        payload = {
            "FilePath": relative_path,
            "UploadId": multipart_info.upload_id,
            "Parts": [{"PartNumber": p.PartNumber, "ETag": p.ETag} for p in e_tags],
        }
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(payload)
        response = await asyncio.to_thread(
            requests.post,
            url,
            params=params,
            headers=headers,
            data=data
        )
        response.raise_for_status()

    async def upload_file_to_azure(
            self,
            upload_url: str,
            stream: IO,
            total_bytes: int | None = None,
            progress_callback: UploadProgressCallback | None = None,
    ):
        block_ids: List[str] = []
        await self.upload_blocks_to_azure(
            block_ids,
            upload_url,
            stream,
            total_bytes=total_bytes,
            progress_callback=progress_callback,
        )
        headers = {
            'x-ms-blob-content-type': 'application/octet-stream',
            'Connection': 'Keep-Alive',
            'Keep-Alive': '3600'
        }
        commit_url = f"{upload_url}&comp=blocklist"
        xml = '<?xml version="1.0" encoding="utf-8"?><BlockList>' + \
              ''.join(f'<Latest>{id}</Latest>' for id in block_ids) + '</BlockList>'

        body = xml.encode("utf-8")
        headers = {
            "Content-Type": "application/xml",
            "x-ms-blob-content-type": "application/octet-stream",
            "Connection": "Keep-Alive",
            "Keep-Alive": "3600",
        }
        response = requests.put(commit_url, data=body, headers=headers)
        response.raise_for_status()

    async def upload_blocks_to_azure(
            self,
            block_ids: List[str],
            upload_url: str,
            stream: IO,
            total_bytes: int | None = None,
            progress_callback: UploadProgressCallback | None = None,
    ):
        block_size = 4 * 1024 * 1024
        block_id = 0
        sent_total = 0
        safe_base = upload_url.replace(" ", "%20")

        while True:
            chunk = stream.read(block_size)
            if not chunk:
                break

            sent_total += len(chunk)
            if progress_callback and total_bytes:
                progress_callback(sent_total, total_bytes)

            plain = (f"block_{block_id:06d}").encode("utf-8")
            import base64
            base64_block_id = base64.b64encode(plain).decode("utf-8")
            encoded_block_id = quote(base64_block_id, safe="")
            block_upload_url = f"{safe_base}&comp=block&blockid={encoded_block_id}"

            headers = {
                "Connection": "Keep-Alive",
                "Keep-Alive": "3600",
            }

            response = await asyncio.to_thread(
                requests.put,
                block_upload_url,
                data=chunk,
                headers=headers
            )
            response.raise_for_status()

            block_ids.append(base64_block_id)
            block_id += 1

    def _iter_file_range(self, stream: IO, start: int, length: int, buf_size: int = 8 * 1024 * 1024):
        stream.seek(start)
        remaining = length
        while remaining > 0:
            chunk = stream.read(min(buf_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk

    async def upload_parts_to_s3(
            self,
            multipart_info: MultipartFile,
            stream: IO,
            progress_callback: UploadProgressCallback | None = None
    ) -> List[PartETagModel]:

        if not multipart_info or not multipart_info.parts:
            raise ValueError("Multipart file information is invalid or empty.")

        part_etags: List[PartETagModel] = []

        total_size = sum(p.RangeEnd - p.RangeStart + 1 for p in multipart_info.parts)
        sent_total = 0

        CHUNK = 8 * 1024 * 1024  # 8MB

        for part in multipart_info.parts:

            length = part.RangeEnd - part.RangeStart + 1
            print("Uploading part:", part.PartNumber, "size:", length)

            stream.seek(part.RangeStart)

            remaining = length
            part_buffer = bytearray()

            while remaining > 0:
                chunk = stream.read(min(CHUNK, remaining))
                if not chunk:
                    break

                part_buffer.extend(chunk)
                remaining -= len(chunk)

                sent_total += len(chunk)
                if progress_callback:
                    progress_callback(sent_total, total_size)

            headers = {
                "Content-Length": str(len(part_buffer)),
                "Content-Type": "binary/octet-stream"
            }

            response = await asyncio.to_thread(
                self.session.put,
                part.Url,
                data=part_buffer,
                headers=headers
            )

            response.raise_for_status()

            etag = response.headers.get("ETag", "") or ""
            etag = etag.strip().strip('"')

            part_etags.append(
                PartETagModel(
                    PartNumber=part.PartNumber,
                    ETag=etag
                )
            )

        return part_etags

    def _parse_json(self, json_str: str, cls):
        if not json_str:
            return None
        data = json.loads(json_str)
        if isinstance(data, dict) and 'd' in data:
            data = data['d']
        return cls(**data)

    class JsonResponseWrapper:
        def __init__(self, d):
            self.d = d