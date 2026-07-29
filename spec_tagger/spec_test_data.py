class TagData:
    def __init__(self) -> None:
        self.files = set()
        self.features = []
        self.stories = []
        self.steps = []

        self.tag_revisions = {}

    def add_tag(
        self, filename, line, closing_line, tag_type, name, revision, full_tag, content
    ):
        tag_validity = True
        reason = ""
        if filename not in self.files:
            self.files.add(filename)

        tag_partial = tag_type + "~" + name

        if tag_partial not in self.tag_revisions:
            self.tag_revisions[tag_partial] = set()

        self.tag_revisions[tag_partial].add(revision)

        if len(self.tag_revisions[tag_partial] > 1):
            tag_validity = False
            reason = "Multiple revision numbers found for this tag."

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
            "validity": {
                "valid": tag_validity,
                "reason": reason,
            },
        }

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


class SpecTagData(TagData):
    def __init__(self) -> None:
        super().__init__()


class TestTagData(TagData):
    def __init__(self) -> None:
        super().__init__()
