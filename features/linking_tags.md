feat~succesful_linking~1

# Linking Tags Together

Linking occurs in spectagger when spec tags and test tags have been found after crawling over a set of user-specified files.
After crawling, the spec tags are linked with the test tags successfully

feat~invalid_tags_found~1

## Invalid Tags

Invalid tags are found during the linking phase where different types of invalidities can come to the surface.

- Orphaned tags: Where test tags have no spec tag or where spec tags have no test tags.
- Revision Number Mismatch: When the revision number of the tags that share the same identifier are different.
- Test Tags Missing Functions: When test tags have no test function that was found during crawling.
- Duplicate Spec Tags: When two or more tags in the spec are identical, breaking the one-to-many relationship they need to have.
