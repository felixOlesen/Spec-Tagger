def validate_args(args):
    pass


def run(args):
    # PROCESS
    # Classification of git logs
    # - Identify changes where only the spec is updated,
    #   or where only the spec is updated, or where only
    #   the implementation code is updated. But where the
    #   connecting items are updated at a later date.
    #
    #   Parse the git logs from this command:
    #   git log --format='COMMIT %H' --name-only --merges $START..HEAD
    #
    #   Then find out which artifacts are touched based on the path prefix they have
    #   (features/ , tests/ , src/)
    #
    #   Then, Pair spec-only and test-only commits with the earlier code commits they respond to,
    #   producing candidate labelled windows.
    #
    #   Select a window where those clusters are dense. Tag the repo once at the window's start,
    #   verify the tool reports clean.
    #
    #   Pre-register by writing down (before running anything) which commits you expected to show drift and why.
    #
    #   Walk forward sequentially, tagging only what's new, running the tool at each step wit --base as the parent and --head
    #   as the commit.
    #
    #   Adjudicate findings against your pre-registered expectations.

    pass
