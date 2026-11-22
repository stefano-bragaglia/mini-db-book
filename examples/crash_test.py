"""Kill a process that is committing transfers, recover its database, and check the total.

Every transfer is either entirely present or entirely absent, so the total
must always be what it was at the start.
"""

import subprocess
import sys
import tempfile
import time

from examples.crash_child import ACCOUNTS
from examples.crash_child import START
from examples.crash_child import open_db


def main() -> None:
    """Kill and recover the child five times, checkpointing once in between."""
    folder = tempfile.mkdtemp()
    for round_ in range(5):
        child = subprocess.Popen(  # noqa: S603 - runs this interpreter on our own module
            [sys.executable, "-m", "examples.crash_child", folder], stdout=subprocess.PIPE, text=True
        )
        assert child.stdout is not None
        child.stdout.readline()  # wait for "ready"
        time.sleep(0.2 + round_ * 0.1)
        child.kill()  # SIGKILL: no cleanup at all
        child.wait()
        child.stdout.close()
        db = open_db(folder)
        total = sum(int(r["bal"] or 0) for r in db.select("acct"))
        print(f"round {round_}: recovered commit {db.commit_seq:>5}, total = {total}")
        assert total == ACCOUNTS * START
        if round_ == 2:
            db.checkpoint()  # also survive a kill after a checkpoint
        db.close()


if __name__ == "__main__":
    main()
