protoc proto/office.proto --go_out=plugins=grpc:.
protoc --proto_path=proto --python_out=proto proto/office.proto