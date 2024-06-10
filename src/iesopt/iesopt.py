from pathlib import Path

from .util import logger, get_iesopt_module_attr
from .julia.util import jl_symbol
from .model import Model, ModelStatus


def run(filename: str | Path, verbosity: bool | str = True, **kwargs) -> Model:
    r"""
    Generate and optimize an IESopt model.

    Results can be accessed (after a successful optimization) using `model.results`.

    Arguments:
        filename (str): Path to the IESopt model file to load.
        verbosity (bool or str, optional): Verbosity level for the IESopt model, defaults to `True`. If `True`, the core
            model will be run in verbose mode, `"warning"` will show warnings (and errors), setting it to `False` will
            only show errors. If `verbosity_solve` is not set in the top-level YAML config, `verbosity = True` will
            enable solver verbose mode, otherwise the solver will be run in silent mode.

    Keyword Arguments:
        **kwargs: Additional keyword arguments to pass to the `Model` constructor.

    Returns:
        Model: The generated and optimized IESopt model.

    Example:
        ..  code-block:: python
            :caption: Run an IESopt model

            import iesopt
            iesopt.run("opt/config.iesopt.yaml")
    """
    model = Model(filename, verbosity=verbosity, **kwargs)
    model.generate()

    if model.status == ModelStatus.GENERATED:
        model.optimize()
    else:
        logger.error("Model could not be generated; skipping optimization.")

    return model


def examples() -> list[str]:
    """
    Return a list of all available examples.

    Returns:
        list[str]: List of available examples. This contains the names of the examples, not the full filenames (so,
            e.g., `"some_example"` instead of `"some_example.iesopt.yaml"`)
    """
    import os

    julia = get_iesopt_module_attr("julia")
    folder = Path(julia.IESoptLib.get_path(jl_symbol("examples")))
    return sorted([fn.split(".iesopt.yaml")[0] for fn in os.listdir(folder) if fn.endswith(".iesopt.yaml")])


def make_example(example: str, dst_dir: str | Path = "./", dst_name: str | None = None) -> Path:
    """
    Generate a local copy of a specific example.

    A list of examples, and their exact names, can be obtained using :py:func:`iesopt.examples()`.

    Arguments:
        example (str): Name of the example to generate.
        dst_dir (str, optional): Directory to generate the example in, defaults to `"./"`.
        dst_name (str, optional): Name of the generated example file (without the ".iesopt.yaml" extension), e.g.,
            `"config"`, will create `dst_dir/config.iesopt.yaml`. Will default to the original name of the example.

    Returns:
        Path: Path to the generated example file.
    """
    import shutil
    import os
    import stat

    julia = get_iesopt_module_attr("julia")
    folder = Path(julia.IESoptLib.get_path(jl_symbol("examples")))

    filename = folder / f"{example}.iesopt.yaml"
    datafolder = folder / "files"
    target_filename = Path(dst_dir) / ((example if dst_name is None else dst_name) + ".iesopt.yaml")
    target_datafolder = Path(dst_dir) / "files"

    # Check if data folder already exists.
    if not os.path.exists(target_datafolder):
        logger.info("Data folder for examples does not exist; creating it, and copying contents")
        shutil.copytree(datafolder, target_datafolder)
    else:
        logger.info("Data folder for examples already exists; NOT copying ANY contents")

    # Copy the config file.
    logger.info("Creating example ('%s') at: '%s'" % (example, target_filename))
    shutil.copy(filename, target_filename)

    # Make everything editable.
    logger.info(
        "Set write permissions for example ('%s'), and data folder ('%s')" % (target_filename, target_datafolder)
    )
    os.chmod(target_filename, os.stat(target_filename).st_mode & ~stat.S_IWRITE | stat.S_IWUSR)
    for dirpath, _, filenames in os.walk(target_datafolder):
        os.chmod(dirpath, os.stat(dirpath).st_mode & ~stat.S_IWRITE | stat.S_IWUSR)
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            os.chmod(filepath, os.stat(filepath).st_mode & ~stat.S_IWRITE | stat.S_IWUSR)

    return target_filename
