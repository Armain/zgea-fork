import pickle
from functools import wraps
from pathlib import Path
from typeguard import typechecked


@typechecked()
def cached(cache_dir_path: Path):
    def inner_cached(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_dir_path.exists():
                ret = func(*args, **kwargs)

                cache_dir_path.parent.mkdir(parents=True, exist_ok=True)
                with cache_dir_path.open("wb") as f:
                    pickle.dump(ret, f)

            else:
                with cache_dir_path.open("rb") as f:
                    ret = pickle.load(f)

            return ret

        return wrapper
    return inner_cached
