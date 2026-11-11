"""Writing the INI configuration a trestle task reads.

`trestle task` takes its arguments from a config file rather than from the
command line, so every task service writes one to a temporary file. Getting the
escaping right is fiddly enough -- and identical enough between the services --
that it lives here once.
"""

import configparser
import tempfile
from collections.abc import Mapping


def escape_for_trestle(value: str) -> str:
    """Escape a value for the interpolation trestle reads the config with.

    trestle reads task configuration with `ExtendedInterpolation`, which treats
    `$` as the start of a reference and rejects anything that is not `$$` or
    `${...}`. A title of "Cost $5" would fail there with
    `InterpolationSyntaxError`, pointing at a temporary file the caller never
    sees. `%` needs nothing: it is only special to `BasicInterpolation`, which
    trestle does not use.

    Args:
        value: The configuration value as the caller gave it.

    Returns:
        The value with `$` doubled, which ExtendedInterpolation reads back as a
        single `$`.
    """
    return value.replace("$", "$$")


def write_task_config(
    section: str,
    values: Mapping[str, str],
    prefix: str,
) -> str:
    """Write one task section to a temporary INI file and return its path.

    The writer is built with `interpolation=None`. The default
    `BasicInterpolation` validates on *write*, so a value containing `%` -- a
    percent-encoded path such as `x%20y.json`, or a title like "100% coverage"
    -- raised `ValueError` from the assignment, before any try block, and
    escaped the service as an exception instead of a readable error message.
    Writing without interpolation leaves `%` alone, and `escape_for_trestle`
    handles the character that does matter to the reader.

    The file is written as UTF-8 because trestle reads it as UTF-8
    (`const.FILE_ENCODING`). Left to the locale, a non-ASCII title would fail or
    silently round-trip wrong anywhere the locale is not UTF-8.

    Args:
        section: Section name, e.g. "task.csv-to-oscal-cd".
        values: Configuration keys and values for that section.
        prefix: Filename prefix, so a leaked temporary file names its service.

    Returns:
        Path to the written file. The caller owns it and must delete it.
    """
    config = configparser.ConfigParser(interpolation=None)
    config[section] = {key: escape_for_trestle(value) for key, value in values.items()}

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".ini",
        delete=False,
        prefix=prefix,
    ) as tmp:
        config.write(tmp)
        return tmp.name
