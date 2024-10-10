import logging
import click
from datetime import datetime 
from pathlib import Path

from .general import produce_dir

divider = "*" * 80

def config_root_logger(log_dir: Path, verbose=False) -> None:
    """
    Configure the root logger

    For this project, this will be the *only* logger that has handlers.
    All other loggers that are generated will propagate their logging
    records to the root logger for them to be handled.

    """

    # Formatting defaults
    DATE_FORMAT = "%Y-%m-%d %H:%M"
    STREAM_FORMAT = "%(message)s"
    FILE_FORMAT = "[%(asctime)s][%(levelname)s] %(name)s %(message)s"

    # Set an overall level
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(STREAM_FORMAT)
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)  # adds to root
    
    # Add file handler
    log_dir = produce_dir(log_dir)
    log_path = f"{log_dir}/{datetime.today().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_path)
    file_formatter = logging.Formatter(FILE_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler)  # adds to root
    

def format_cli_flags(args, params) -> str:
  """
  Formats Click context arguments and parameters for human-readable logging.

  Args:
      args (list): List of positional arguments.
      params (dict): Dictionary of keyword arguments.

  Returns:
      str: Formatted string representing the flags.
  """
  flag_strs = []
  for arg in args:
    flag_strs.append(arg)
  for key, value in params.items():
    flag_strs.append(f"--{key}" + (f" {value}" if value else ""))
  return " ".join(flag_strs)


def identify_cli_command() -> str:
    """
    Identify the CLI command being run.

    Returns:
        str: CLI options to run script
    """
    ctx = click.get_current_context()
    flags = format_cli_flags(ctx.args, ctx.params)
    return f"{ctx.command.name} {flags})"
    
