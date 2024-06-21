import requests

from google.protobuf.json_format import MessageToJson, MessageToDict, Parse
import proto.office_pb2 as pb
from errs import INVALID_FORMAT_ERR, FAILED_TO_CONNECT
import json


class Api:
    def __init__(self, host: str):
        self.host = host
        self.url = f"http://{self.host}"
        self.session = requests.Session()

    def create_doc(self, req: pb.CreateDocumentRequest) -> (pb.CreateDocumentResponse, str):
        try:
            d = MessageToJson(req)
            r = self.session.post(f"{self.url}/api/docs/create", data=d)
        except Exception as e:
            print("failed to create doc")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return Parse(r.text, pb.CreateDocumentResponse()), None
        except Exception as e:
            print("failed to create doc")
            print(e)
            return None, INVALID_FORMAT_ERR

    def list_doc(self, req: pb.ListDocumentsRequest) -> (pb.ListDocumentsResponse, str):
        try:
            d = MessageToJson(req)
            r = self.session.post(f"{self.url}/api/docs/list", data=d)
        except Exception as e:
            print("failed to list docs")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return Parse(r.text, pb.ListDocumentsResponse()), None
        except Exception as e:
            print("failed to list docs")
            print(e)
            return None, INVALID_FORMAT_ERR

    def execute_doc(self, req: pb.ExecuteRequest) -> (pb.ExecuteResponse, str):
        try:
            d = {
                "doc_id": int(req.doc_id),
                "token": req.token,
            }
            r = self.session.post(f"{self.url}/api/docs/execute", data=json.dumps(d))
        except Exception as e:
            print("failed to execute doc")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return json.loads(r.text), None
        except Exception as e:
            print("failed to execute doc")
            print(e)
            return None, INVALID_FORMAT_ERR

    def test_doc(self, req: pb.ExecuteRequest) -> (pb.ExecuteResponse, str):
        try:
            d = {
                "content": req.content,
            }
            r = self.session.post(f"{self.url}/api/docs/test", data=json.dumps(d))
        except Exception as e:
            print("failed to test doc")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return json.loads(r.text), None
        except Exception as e:
            print("failed to test doc")
            print(e)
            return None, INVALID_FORMAT_ERR

    def login(self, req: pb.LoginRequest) -> (pb.LoginResponse, str):
        try:
            d = MessageToJson(req)
            r = self.session.post(f"{self.url}/api/users/login", data=d)
        except Exception as e:
            print("failed to login doc")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return None
        except Exception as e:
            print("failed to login doc")
            print(e)
            return INVALID_FORMAT_ERR

    def register(self, req: pb.RegisterRequest) -> (pb.RegisterResponse, str):
        try:
            d = MessageToJson(req)
            r = self.session.post(f"{self.url}/api/users/register", data=d)
        except Exception as e:
            print("failed to register doc")
            print(e)
            return FAILED_TO_CONNECT
        try:
            return None
        except Exception as e:
            print("failed to register doc")
            print(e)
            return INVALID_FORMAT_ERR

    def list_users(self, req: pb.ListRequest) -> (pb.ListResponse, str):
        try:
            d = MessageToJson(req)
            r = self.session.post(f"{self.url}/api/users/list", data=d)
        except Exception as e:
            print("failed to list users")
            print(e)
            return None, FAILED_TO_CONNECT
        try:
            return Parse(r.text, pb.ListResponse()), None
        except Exception as e:
            print("failed to list users")
            print(e)
            return None, INVALID_FORMAT_ERR
