import json

from core.ml.trainer import XGBTrainer


if __name__ == "__main__":
    trainer = XGBTrainer()

    result = trainer.train(
        force=True
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )
