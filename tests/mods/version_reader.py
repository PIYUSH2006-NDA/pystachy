from sys import version_info


def version() -> tuple[int, int, int, str, int]:
    return version_info
