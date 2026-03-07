from dunamai import Version


def get_version() -> str:
    """
    Autodetect VCS and get the version
    """
    version = Version.from_any_vcs()
    return version.serialize(
        metadata=True,
        dirty=True,
    )


__version__ = get_version()
