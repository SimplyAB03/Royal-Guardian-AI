from __future__ import annotations
import argparse, time
from royal_guardian.db.base import SessionLocal, init_db
from royal_guardian.services.workflows import process_queue

def main():
    parser=argparse.ArgumentParser(description="Royal Guardian durable workflow worker")
    parser.add_argument("--once",action="store_true")
    parser.add_argument("--interval",type=float,default=2.0)
    args=parser.parse_args(); init_db()
    while True:
        with SessionLocal() as db: process_queue(db)
        if args.once: break
        time.sleep(max(args.interval,0.25))

if __name__=="__main__": main()
