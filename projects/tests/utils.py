from uuid import uuid4
from projects.models import Tag

TEST_PROJ_NAME = f'Test Project {uuid4().hex}'
TEST_PROJ_REPO = f'test-project'
TEST_IMAGE = f"testimage{uuid4().hex}.png"
TEST_TAG = f'test_tag_{uuid4().hex}'
TEST_DESC = f"{uuid4().hex} {uuid4().hex} {uuid4().hex}"
TEST_CATEGORY = f'Test category {uuid4().hex}'

def getTestTags(count=1,start=0):
    topics = []
    for i in range(count):
        topics.append(f"test_tag_{i+start}{uuid4().hex}")
    return topics

def getTestTagsInst(count=1,start=0):
    tags = []
    for name in getTestTags(count,start):
        tags.append(Tag(name=name))
    return tags
