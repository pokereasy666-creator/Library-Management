from fastapi.encoders import jsonable_encoder


class BizError(Exception):
    """业务异常：由全局异常处理器转成 {code, msg, data}，HTTP 状态码与 code 一致。"""

    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code
        self.msg = msg


def ok(data=None, msg: str = "操作成功") -> dict:
    return {"code": 200, "msg": msg, "data": jsonable_encoder(data)}
