class Linker:
    def __init__(self, specData, testData):
        self.specData = specData
        self.testData = testData
        self.invalidTags = []
        self.linkedTags = {}
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
        for tag in self.specData:
            print(tag)
        print("\nTest Data:")
        for tag in self.testData:
            print(tag)

        # Display linked tags
        print("\nLinked Tags:")
        for key, value in self.linkedTags.items():
            print(f"Spec Tag: {value['spec_tag']}")
            for test_tag in value['test_tags']:
                print(f"  Test Tag: {test_tag}")

        # Display invalid tags
        print("\nInvalid Tags:")
        for invalid in self.invalidTags:
            print(invalid)
        
    
    def link_data(self):
        self.check_tag_frequency_and_revisions(self.specData)
        specTestMap = {}

        for spec_tag in self.specData:
            specTestMap[spec_tag['type'] + '~' + spec_tag['name']] = {'spec_tag': spec_tag, 'test_tags': []}

        # if  

        for test_tag in self.testData:
            if test_tag['type'] + '~' + test_tag['name'] not in specTestMap:
                self.invalidTags.append({'tag':test_tag['full_tag'], 'reason':'Test tag has no corresponding spec tag.'})
            else:
                specTestMap[test_tag['type'] + '~' + test_tag['name']]['test_tags'].append(test_tag)
                print(f"Linked test tag {test_tag['full_tag']} to spec tag {specTestMap[test_tag['type'] + '~' + test_tag['name']]['spec_tag']['full_tag']}")

        # check revision numbers and add invalid tags for mismatches
        for key, value in specTestMap.items():
            spec_tag = value['spec_tag']
            test_tags = value['test_tags']
            if not test_tags:
                self.invalidTags.append({'tag':spec_tag['full_tag'], 'reason':'Spec tag has no corresponding test tag.'})
                specTestMap[key]['test_tags'] = None
            else:
                for test_tag in test_tags:
                    if spec_tag['revision'] != test_tag['revision']:
                        self.invalidTags.append({'tag':test_tag['full_tag'], 'reason':'Revision number mismatch with spec tag.'})
                        # if the revision number of the test tag does not match the spec tag, remove it from the list of test tags
                        specTestMap[key]['test_tags'].remove(test_tag)
        
        # remove any entries from specTestMap where the test_tags list is empty
        specTestMap = {k: v for k, v in specTestMap.items() if v['test_tags'] is not None and len(v['test_tags']) > 0}
        
        self.linkedTags = specTestMap


    def check_tag_frequency_and_revisions(self, tagData):
        tagFreqMap = {}
        tagRevisionMap = {}
        for tag in tagData:
            tag_key = tag['type'] + '~' + tag['name']
            if tag['full_tag'] not in tagFreqMap:
                tagFreqMap[tag['full_tag']] = 0
            
            if tag_key not in tagRevisionMap:
                tagRevisionMap[tag_key] = set()
            
            tagFreqMap[tag['full_tag']] += 1
            tagRevisionMap[tag_key].add(tag['revision'])

            if tagFreqMap[tag['full_tag']] > 1:
                self.invalidTags.append({'tag':tag['full_tag'], 'reason':'Duplicate tag found.'})

            if len(tagRevisionMap[tag_key]) > 1:
                # print the smallest revision number for the tag
                smallest_revision = min(tagRevisionMap[tag_key], key=int)
                highest_revision = max(tagRevisionMap[tag_key], key=int)
                self.invalidTags.append({'tag':tag_key+'~'+smallest_revision, 'reason':'Multiple revisions found for the same tag: ' + ', '.join(tagRevisionMap[tag_key]) + '. Using revision: ' + highest_revision})
                # set the highest revision number as the valid one
                tagRevisionMap[tag_key] = {highest_revision}