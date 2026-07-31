class TagData:
    def __init__(self) -> None:
        self.files = set()
        self.features = []
        self.stories = []
        self.steps = []
        self.file_to_tag = {}
        self.tag_revisions = {}

    def add_tag(
        self,
        filename,
        line,
        closing_line,
        tag_type,
        name,
        revision,
        full_tag,
        content,
        item_start_line,
    ):
        tag_validity = True
        reason = []
        if filename not in self.files:
            self.files.add(filename)

        if filename not in self.file_to_tag:
            self.file_to_tag[filename] = []

        tag_partial = tag_type + "~" + name

        if tag_partial not in self.tag_revisions:
            self.tag_revisions[tag_partial] = set()

        self.tag_revisions[tag_partial].add(revision)

        if len(self.tag_revisions[tag_partial]) > 1:
            tag_validity = False
            reason = ["Multiple revision numbers found for this tag."]

        if tag_type == "feat" or tag_type == "story":
            closing_line = line + 10

        tag = {
            "filename": filename,
            "line": line,
            "closing_line": closing_line,
            "type": tag_type,
            "name": name,
            "revision": revision,
            "full_tag": full_tag,
            "tag_partial": tag_partial,
            "content": content,
            "item_start_line": item_start_line,
            "validity": {
                "valid": tag_validity,
                "reasons": reason,
            },
        }

        self.file_to_tag[filename].append(tag)
        match tag_type:
            case "feat":
                self.features.append(tag)
            case "story":
                self.stories.append(tag)
            case "step":
                self.steps.append(tag)
            case _:
                pass

    def get_tag(self, search_tag: str) -> dict | None:
        if search_tag.startswith("feat"):
            for feature in self.features:
                if feature["full_tag"] == search_tag:
                    return feature
        elif search_tag.startswith("story"):
            for story in self.stories:
                if story["full_tag"] == search_tag:
                    return story
        elif search_tag.startswith("step"):
            for step in self.steps:
                if step["full_tag"] == search_tag:
                    return step
        return None

    def get_most_recent_revision(self, tag_partial: str):
        return max(self.tag_revisions[tag_partial])

    def update_closing_line(self, search_tag: str, line_number: int):
        tag = self.get_tag(search_tag)
        if tag:
            tag["closing_line"] = line_number
        else:
            print("Warning, cannot update closing line, tag not found.")

    def get_all_tags(self) -> list[dict]:
        full_list = []
        full_list.extend(self.features)
        full_list.extend(self.stories)
        full_list.extend(self.steps)

        return full_list


class SpecTagData(TagData):
    def __init__(self) -> None:
        super().__init__()

    def update_spec_item_closing_lines(self):
        if len(self.features) > 1:
            for i in range(len(self.features) - 1):
                feature = self.features[i]
                next_feature = self.features[i + 1]
                if feature["filename"] == next_feature["filename"]:
                    feature["closing_line"] = next_feature["line"]
                else:
                    feature["closing_line"] = -1
                if i == len(self.features) - 2:
                    next_feature["closing_line"] = -1
        elif len(self.features) == 1:
            self.features[0]["closing_line"] = -1

        if len(self.stories) > 1:
            for i in range(len(self.stories) - 1):
                story = self.stories[i]
                next_story = self.stories[i + 1]
                if story["filename"] == next_story["filename"]:
                    story["closing_line"] = next_story["line"]
                else:
                    story["closing_line"] = -1
                if i == len(self.stories) - 2:
                    next_story["closing_line"] = -1
        elif len(self.stories) == 1:
            self.stories[0]["closing_line"] = -1

    def identify_duplicates(self):
        all_tags = self.get_all_tags()
        freq_map = {}
        for tag in all_tags:
            if tag["full_tag"] not in freq_map:
                freq_map[tag["full_tag"]] = []
            freq_map[tag["full_tag"]].append(tag)

        for _, tag_info in freq_map.items():
            if len(tag_info) > 1:
                for tag in tag_info:
                    tag["validity"]["valid"] = False
                    tag["validity"]["reasons"].append(
                        "Duplicate tags found in the specification."
                    )


class TestTagData(TagData):
    def __init__(self) -> None:
        super().__init__()
