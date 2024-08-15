import json
from typing import Any, cast

import cbor2
import msgpack
import orjson
import ormsgpack


class BaseEncoder:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __call__(self, payload: Any) -> bytes:
        raise NotImplementedError


class BaseDecoder:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __call__(self, payload: bytes) -> Any:
        raise NotImplementedError


class NoneEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return payload


class NoneDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return payload


class StrEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return str(payload).encode(*self.args, **self.kwargs)


class StrDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return payload.decode(*self.args, **self.kwargs)


class JsonEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return json.dumps(payload, *self.args, **self.kwargs).encode()


class JsonDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return json.loads(payload, *self.args, **self.kwargs)


class CborEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return cbor2.dumps(payload, *self.args, **self.kwargs)


class CborDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return cbor2.loads(payload, *self.args, **self.kwargs)


class MsgPackEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return cast(bytes, msgpack.packb(payload, *self.args, **self.kwargs))


class MsgPackDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return msgpack.unpackb(payload, *self.args, **self.kwargs)


class OrJsonEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return orjson.dumps(payload, *self.args, **self.kwargs)


class OrJsonDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return orjson.loads(payload, *self.args, **self.kwargs)


class OrMsgPackEncoder(BaseEncoder):
    def __call__(self, payload: Any) -> bytes:
        return ormsgpack.packb(payload, *self.args, **self.kwargs)


class OrMsgPackDecoder(BaseDecoder):
    def __call__(self, payload: bytes) -> Any:
        return ormsgpack.unpackb(payload, *self.args, **self.kwargs)
