class Linker:
    def __init__(self, spec_data, test_data):
        self.spec_data = spec_data
        self.test_data = test_data
        self.invalid_tags = []
        self.linked_tags = {}
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
        print("Spec Data:")
        for tag in self.spec_data:
            print(tag)
        print("\nTest Data:")
        for tag in self.test_data:
            print(tag)

        # Display linked tags
        print("\nLinked Tags:")
        for key, value in self.linked_tags.items():
            print(f"Spec Tag: {value['spec_tag']}")
            for test_tag in value['test_tags']:
                print(f"  Test Tag: {test_tag}")

        # Display invalid tags
        print("\nInvalid Tags:")
        for invalid in self.invalid_tags:
            print(invalid)
        
    
    def link_data(self):
        self.check_tag_frequency_and_revisions(self.spec_data)

        for spec_tag in self.spec_data:
            self.linked_tags[spec_tag['type'] + '~' + spec_tag['name']] = {'spec_tag': spec_tag, 'test_tags': []}

        for test_tag in self.test_data:
            if test_tag['type'] + '~' + test_tag['name'] not in self.linked_tags:
                self.register_invalid_tag(test_tag, 'Test tag has no corresponding spec tag.')
            elif test_tag['test_function'] is None:
                self.register_invalid_tag(test_tag, 'No test function was found following the tag.')
            else:
                self.linked_tags[test_tag['type'] + '~' + test_tag['name']]['test_tags'].append(test_tag)
                print(f"Linked test tag {test_tag['full_tag']} to spec tag {self.linked_tags[test_tag['type'] + '~' + test_tag['name']]['spec_tag']['full_tag']}")

        # check revision numbers and add invalid tags for mismatches
        for key, value in self.linked_tags.items():
            spec_tag = value['spec_tag']
            test_tags = value['test_tags']
            if not test_tags:
                self.register_invalid_tag(spec_tag, 'Spec tag has no corresponding test tag.')
                self.linked_tags[key]['test_tags'] = None
            else:
                for test_tag in test_tags:
                    if spec_tag['revision'] != test_tag['revision']:
                        self.register_invalid_tag(test_tag, 'Revision number mismatch with spec tag.')
                        # if the revision number of the test tag does not match the spec tag, remove it from the list of test tags
                        self.linked_tags[key]['test_tags'].remove(test_tag)
        
        # remove any entries from linked_tags where the test_tags list is empty
        self.linked_tags = {k: v for k, v in self.linked_tags.items() if v['test_tags'] is not None and len(v['test_tags']) > 0}

        return self.linked_tags

    def check_tag_frequency_and_revisions(self, tag_data):
        tag_freq_map = {}
        tag_revision_map = {}
        for tag in tag_data:
            tag_key = tag['type'] + '~' + tag['name']
            if tag['full_tag'] not in tag_freq_map:
                tag_freq_map[tag['full_tag']] = 0
            
            if tag_key not in tag_revision_map:
                tag_revision_map[tag_key] = set()
            
            tag_freq_map[tag['full_tag']] += 1
            tag_revision_map[tag_key].add(tag['revision'])

            if tag_freq_map[tag['full_tag']] > 1:
                self.register_invalid_tag(tag, 'Duplicate tag found.')

            if len(tag_revision_map[tag_key]) > 1:
                # print the smallest revision number for the tag
                smallest_revision = min(tag_revision_map[tag_key], key=int)
                highest_revision = max(tag_revision_map[tag_key], key=int)
                # search for correct tag in tag_data to 
                invalid_tag = tag_key+'~'+smallest_revision
                for tag in tag_data:
                    if tag['full_tag'] == invalid_tag:
                        self.register_invalid_tag(tag, 'Multiple revisions found for the same tag: ' + ', '.join(tag_revision_map[tag_key]) + '. Using revision: ' + highest_revision)
                        break
                # set the highest revision number as the valid one
                tag_revision_map[tag_key] = {highest_revision}
    
    def register_invalid_tag(self, tag, reason):
        self.invalid_tags.append({'tag':tag['full_tag'], 'file':tag['filename'], 'line':tag['line'], 'reason':reason})
