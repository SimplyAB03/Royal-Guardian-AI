from __future__ import annotations

import argparse

from endpoint.client import enroll, load_config, once, run_forever

parser = argparse.ArgumentParser(description="Royal Guardian Endpoint")
sub = parser.add_subparsers(dest="command", required=True)

e = sub.add_parser("enroll")
e.add_argument("--server", required=True)
e.add_argument("--token", required=True)
e.add_argument("--name")
sub.add_parser("once")
r = sub.add_parser("run")
r.add_argument("--interval", type=int, default=20)

args = parser.parse_args()
if args.command == "enroll":
    cfg = enroll(args.server, args.token, args.name)
    print(f"Enrolled device {cfg['device_id']}")
elif args.command == "once":
    once(load_config())
elif args.command == "run":
    run_forever(args.interval)
