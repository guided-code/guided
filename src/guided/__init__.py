from dunamai import Version
from importlib.metadata import version


def get_version() -> str:
    """
    Autodetect VCS and get the version
    """
    try:
        semver = Version.from_any_vcs()
        return semver.serialize(
            metadata=True,
            dirty=True,
        )
    except RuntimeError:
        return version("guided")


__version__ = get_version()
