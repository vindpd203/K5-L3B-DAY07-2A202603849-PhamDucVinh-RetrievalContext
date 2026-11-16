"""GLMController + starter run_agent with a scripted fake OpenAI client (code check only, not a benchmark)."""
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, "starter")
from agentic import run_agent  # noqa: E402

from src.agent import GLMController, normalize_citations  # noqa: E402

CID = "TT-91-2026:A:p004:00"
CHUNK = {"id": CID, "text": "Ký hiệu hóa đơn điện tử là nhóm sáu ký tự", "source_id": "TT-91-2026",
         "source": "tt.pdf", "page": 4, "metadata": {}, "score": 0.8}


def reply(content=None, query=None):
    calls = [NS(function=NS(name="search", arguments=f'{{"query": "{query}"}}'))] if query else None
    return NS(choices=[NS(message=NS(content=content, tool_calls=calls), finish_reason="stop")],
              model="fake", usage=NS(prompt_tokens=10, completion_tokens=5))


class FakeClient:
    def __init__(self, replies):
        self.replies, self.requests = list(replies), []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.requests.append(kw)
        return self.replies.pop(0)


class Retriever:
    def search(self, query, *, filters=None, top_k=3):
        return [CHUNK]


class AgentTests(unittest.TestCase):
    def run_with(self, replies, max_searches=2):
        client = FakeClient(replies)
        ctl = GLMController(max_searches, client=client, model="fake")
        return run_agent("Ký hiệu gồm mấy ký tự?", ctl, Retriever(), max_searches=max_searches, top_k=3,
                         budget=3000), ctl, client

    def test_search_then_cited_answer(self):
        res, ctl, client = self.run_with([reply(query="ký hiệu hóa đơn"), reply(f"Sáu ký tự [{CID}].")])
        self.assertEqual(res["status"], "answered")
        self.assertEqual(res["citations"], [CID])
        self.assertIn(CID, client.requests[1]["messages"][1]["content"])  # context reached the model

    def test_model_abstains_without_citation(self):
        res, ctl, _ = self.run_with([reply(query="mức phạt"), reply("Không đủ bằng chứng trong tài liệu để trả lời.")])
        self.assertEqual(res["status"], "abstain")
        self.assertTrue(ctl.calls[-1]["model_abstained"])

    def test_invented_citation_is_rejected(self):
        res, _, _ = self.run_with([reply(query="x"), reply("Sáu ký tự [TT-91-2026:A:p999:09].")])
        self.assertEqual(res["status"], "abstain")

    def test_no_tools_offered_after_search_limit(self):
        _, _, client = self.run_with([reply(query="a"), reply(f"Sáu [{CID}]")], max_searches=1)
        self.assertIn("tools", client.requests[0])
        self.assertNotIn("tools", client.requests[1])

    def test_first_query_original_skips_model_call(self):
        client = FakeClient([reply(f"Sáu ký tự [{CID}].")])
        ctl = GLMController(2, client=client, model="fake", first_query="original")
        res = run_agent("Ký hiệu gồm mấy ký tự?", ctl, Retriever(), max_searches=2, top_k=3, budget=3000)
        self.assertEqual(res["status"], "answered")
        self.assertEqual(len(client.requests), 1)  # only the answer call
        self.assertEqual(res["events"][0]["query"], "Ký hiệu gồm mấy ký tự?")

    def test_combined_brackets_are_split(self):
        a, ids = normalize_citations(f"x [{CID}, TT-91-2026:A:p003:01] y [1]")
        self.assertEqual(ids, [CID, "TT-91-2026:A:p003:01"])
        self.assertIn(f"[{CID}][TT-91-2026:A:p003:01]", a)
        self.assertIn("[1]", a)  # non-id brackets untouched


if __name__ == "__main__":
    unittest.main()
