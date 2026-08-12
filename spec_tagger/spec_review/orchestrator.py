from pathlib import Path
import os
from dotenv import load_dotenv
from spec_tagger.ai.anthropic_controller import AnthropicController
from spec_tagger.ai.prompt_construction import PromptConstructor
from spec_tagger.spec_review.context_aggregator import ContextAggregator
from spec_tagger.spec_review.result_triage import ResultTriage
from spec_tagger.ai.litellm_controller import LiteLLMController


def validate_args(args):
    if not args.report_input:
        raise ValueError(f"report_input '{args.report_input}' is none")
    if args.report_input and not Path.is_file(args.report_input):
        raise ValueError(f"report_iput '{args.report_input}' file does not exist")


def run(args):
    validate_args(args)
    # Aggregate Context
    aggregator = ContextAggregator(args.report_input)
    collected_context = aggregator.get_all_context()
    git_global_context = aggregator.git_context_data
    # Classify Problem
    triage = ResultTriage(collected_context)
    solutions = triage.filter_results()
    for solution in solutions:
        solution.display_data()
    # Construct Prompt OR NO-AI Method
    if not args.no_ai:
        prompt_constructor = PromptConstructor(solutions, git_global_context)
        prompts = prompt_constructor.construct_prompt_list()
        ai_controller = LiteLLMController(
            args.model_provider, args.model_name, args.rate_limit
        )
        drifted_tags = []
        # for prompt in prompts:
        for prompt in prompts:
            response, usage_info, cost_usd = ai_controller.send_prompt(
                prompt.schema,
                prompt.context_evidence,
                prompt.system_prompt,
            )
            if response:
                if "drifted" in response and response.drifted:
                    drifted_tags.append(response)
            ai_controller.parse_response(response, usage_info, cost_usd)
            ai_controller.show_total_session_token_usage()
        for drifted in drifted_tags:
            print(f"-----FOUND DRIFT-----\n{drifted}")
    # Prepare output suggestion
    # Feed into workflow for PR OR Print to STDOUT
