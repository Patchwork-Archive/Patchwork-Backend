import functools

def retry(max_attempts):
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
            raise RuntimeError(f"Function '{func.__name__}' failed after {max_attempts} attempts.")
        return wrapper_retry
    return decorator_retry