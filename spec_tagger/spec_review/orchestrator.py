from pathlib import Path


def validate_args(args):
    if not args.report_path:
        raise ValueError(f"report_path '{args.report_path}' is none")
    if args.report_path and not Path.is_file(args.report_path):
        raise ValueError(f"report_path '{args.report_path}' file does not exist")


def run(args):
    validate_args(args)
    # Setup
    # Aggregate Context
    # Classify Problem
    # Construct Prompt OR NO-AI Method
    # Prepare output suggestion
    # Feed into workflow for PR OR Print to STDOUT
