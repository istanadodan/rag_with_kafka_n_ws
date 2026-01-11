# 파라미터 serializing
def join_all_params(*args, **kwargs) -> str:
    args_repr = ",".join(map(repr, args) if args else "")
    kwargs_repr = ",".join(f"{k}={v!r}" for k, v in kwargs.items()) if kwargs else ""
    return f"{args_repr},{kwargs_repr}"
