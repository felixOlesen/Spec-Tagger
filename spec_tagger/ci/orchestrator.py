from spec_tagger.ci.result_classifier import ResultClassifier
from spec_tagger.ci.context_aggregator import ContextAggregator
from pathlib import Path


def validate_args(args):
    if not args.report_path:
        raise ValueError(f"report_path '{args.report_path}' is none")
    if args.report_path and not Path.is_file(args.report_path):
        raise ValueError(f"report_path '{args.report_path}' file does not exist")


def run(args):
    validate_args(args)
    # result classification
    classifier = ResultClassifier(args.report_path)
    classified_results = classifier.classify_results()

    # context aggregation for each result
    aggregator = ContextAggregator(classified_results)

    # prompting AI if available
    # constructing feedback and changes
    pass
