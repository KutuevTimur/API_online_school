"""Run only as: python -m src.modules.integrations_vk --mode offline."""

import argparse
import json

from .fixtures import FakeClock, FixturePlatform, TRUSTED_CHILD, event
from .offline import OfflineAdapter, OfflineConfig, TemporaryJsonStore


def main():
    parser = argparse.ArgumentParser(description="F01.1 synthetic offline harness")
    parser.add_argument("--mode", required=True, choices=["offline"])
    args = parser.parse_args()
    config = OfflineConfig(mode=args.mode)
    config.validate()
    with TemporaryJsonStore() as store:
        adapter = OfflineAdapter(config, store, FakeClock(), FixturePlatform())
        key = adapter.admit(event({"action": "menu_open"}), trusted=TRUSTED_CHILD)
        result = adapter.resume(key)
        print(json.dumps({"mode": args.mode, "status": result["status"],
                          "state": result["body"]["state"], "synthetic": True}))


if __name__ == "__main__":
    main()
