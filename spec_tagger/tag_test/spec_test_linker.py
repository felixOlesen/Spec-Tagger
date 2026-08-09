from spec_tagger.tag_test.spec_test_data import SpecTagData, TagData, TestTagData
from enum import Enum


class Invalidities(Enum):
    TAG_REVISION_MISMATCH = (
        "Revision number is outdated compared to other tags with the same identifier."
    )
    DUPLICATE_SPEC_TAG = "Duplicate tags found in the specification."
    NO_SPEC_TAG_FOR_TEST_TAG = "Test tag has no corresponding valid spec tag."
    NO_TEST_TAG_FOR_SPEC_TAG = "Spec tag has no corresponding valid test tag."
    NO_FUNCTION_FOR_TEST_TAG = "No test function was found following the tag."


class Linker:
    def __init__(
        self,
        spec_data: SpecTagData,
        test_data: TestTagData,
        target_tag: str | None,
        verbose: bool,
        spec_subset: bool = False,
    ):
        self.spec_data = spec_data
        self.test_data = test_data
        self.verbose = verbose
        self.invalid_tags = []
        self.linked_tags = {}

        if target_tag:
            target_tag = target_tag.strip()
            tag_group = target_tag.split("~")
            tag_partial = tag_group[0] + "~" + tag_group[1]
            target_tag = tag_partial

        self.target_tag = target_tag
        self.spec_subset = spec_subset

    # Cases to consider:
    # 1. Spec has a tag, but no corresponding test exists.
    # 2. Test has a tag, but no corresponding spec exists.
    # 3. Both spec and test have the same tag, but the revision numbers differ.
    # 4. Both spec and test have the same tag and the same revision number.
    # 5. Spec has multiple tags, and tests exist for some but not all of them.
    # 6. Test has multiple tags, and specs exist for some but not all of them.
    # 7. Spec and test have the same tag, but the spec has a higher revision number than the test.
    # 8. Spec and test have the same tag, but the test has a higher revision number than the spec.

    def display_data(self):
        if self.spec_data:
            print("Spec Data:")
            all_spec_tags = self.spec_data.get_all_tags()
            for tag in all_spec_tags:
                print(tag)
        if self.test_data:
            print("\nTest Data:")
            all_test_tags = self.test_data.get_all_tags()
            for tag in all_test_tags:
                print(tag)

        # Display linked tags
        if self.linked_tags:
            print("\nLinked Tags:")
            for tag_key, value in self.linked_tags.items():
                if value.get("test_tags"):
                    print(f"\nSpec Tag: {value['spec_tag']}")
                    for test_tag in value["test_tags"]:
                        print(f"\n  Test Tag: {test_tag}")
                else:
                    print(f"\nWarning, null link data found for {tag_key}")
        # Display invalid tags
        if self.invalid_tags:
            print("\nInvalid Tags:")
            for invalid in self.invalid_tags:
                print(invalid)

    def display_invalid_tags(self):
        if self.invalid_tags:
            print("\nInvalid Tags:")
            for invalid in self.invalid_tags:
                print(f"Tag: {invalid['full_tag']}")
                print("Reasons:")
                for reason in invalid["validity"]["reasons"]:
                    print(f"  {reason}\n")

    def link_data(self) -> tuple[dict, list] | None:
        if self.target_tag:
            self.filter_out_non_target_tags()
        self.spec_data.identify_duplicates()
        self.check_revisions()
        all_spec_tags = self.spec_data.get_all_tags()
        all_test_tags = self.test_data.get_all_tags()

        if not self.spec_data or not all_spec_tags:
            print("Warning spec data found to be null on run.")
            return

        for spec_tag in all_spec_tags:
            if spec_tag["validity"]["valid"] and "ignore" not in spec_tag:
                self.linked_tags[spec_tag["tag_partial"]] = {
                    "spec_tag": spec_tag,
                    "test_tags": [],
                }

        if not self.test_data or not all_test_tags:
            print("Warning test data found to be null on run.")
            return

        for test_tag in all_test_tags:
            if test_tag["validity"]["valid"] and "ignore" not in test_tag:
                if test_tag["tag_partial"] not in self.linked_tags:
                    self.register_invalid_tag(
                        test_tag, Invalidities.NO_SPEC_TAG_FOR_TEST_TAG
                    )
                elif test_tag["test_function"] is None:
                    self.register_invalid_tag(
                        test_tag, Invalidities.NO_FUNCTION_FOR_TEST_TAG
                    )
                else:
                    self.linked_tags[test_tag["type"] + "~" + test_tag["name"]][
                        "test_tags"
                    ].append(test_tag)
                    if self.verbose:
                        print(
                            f"Linked test tag {test_tag['full_tag']} to spec tag {self.linked_tags[test_tag['tag_partial']]['spec_tag']['full_tag']}"
                        )

        # check revision numbers and add invalid tags for mismatches
        for key, value in self.linked_tags.items():
            spec_tag = value["spec_tag"]
            test_tags = value["test_tags"]
            if not test_tags:
                self.register_invalid_tag(
                    spec_tag, Invalidities.NO_TEST_TAG_FOR_SPEC_TAG
                )
                self.linked_tags[key]["test_tags"] = None

        # remove any entries from linked_tags where the test_tags list is empty
        # self.linked_tags = {
        #    k: v
        #    for k, v in self.linked_tags.items()
        #    if v["test_tags"] is not None and len(v["test_tags"]) > 0
        # }
        self.invalid_tag_sweep()
        if self.verbose:
            self.display_data()

        return self.linked_tags, self.invalid_tags

    def invalid_tag_sweep(self):
        all_tags = self.spec_data.get_all_tags()
        all_tags.extend(self.test_data.get_all_tags())

        for tag in all_tags:
            if not tag["validity"]["valid"] and "ignore" not in tag:
                self.invalid_tags.append(tag)

    def check_revisions(self):
        revision_map = self.spec_data.tag_revisions
        all_tags = self.spec_data.get_all_tags()
        all_tags.extend(self.test_data.get_all_tags())

        test_revisions = self.test_data.tag_revisions
        for tag_partial, revisions in test_revisions.items():
            if tag_partial in revision_map:
                revision_map[tag_partial].update(revisions)

        for tag in all_tags:
            if self.spec_subset and tag["tag_partial"] not in revision_map:
                continue
            revisions = revision_map[tag["tag_partial"]]
            if len(revisions) > 1 and "ignore" not in tag:
                highest_revision = max(revisions)
                if tag["revision"] != highest_revision:
                    self.register_invalid_tag(tag, Invalidities.TAG_REVISION_MISMATCH)

    def register_invalid_tag(self, tag, reason):
        tag["validity"]["valid"] = False
        tag["validity"]["reasons"].append(reason)

    def filter_out_non_target_tags(self):
        all_tags = self.spec_data.get_all_tags()
        all_test_tags = self.test_data.get_all_tags()
        all_tags.extend(all_test_tags)
        for tag in all_tags:
            if tag["tag_partial"] != self.target_tag:
                tag["ignore"] = True
