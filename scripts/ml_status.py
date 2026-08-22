import json

from core.ml.runtime import MLRuntime


if __name__ == "__main__":
    runtime = (
        MLRuntime.get_instance()
    )

    print(
        json.dumps(
            runtime.status(),
            indent=2,
        )
    )
