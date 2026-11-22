"""Run the test suite, and fail if any test fails."""

import unittest


def main() -> None:
    """Load ``tests.test_minidb`` and run it."""
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_minidb")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful()


if __name__ == "__main__":
    main()
