import tempfile
import unittest
from unittest.mock import Mock, patch

from config import ROOT
from timeline_mcp.server import publish_video


class PublishVideoTest(unittest.TestCase):
    def test_uploads_instagram_reel(self):
        response = Mock(ok=True, status_code=200)
        response.json.return_value = {
            "success": True,
            "results": {"instagram": {"url": "https://instagram.test/reel"}},
        }

        with tempfile.NamedTemporaryFile(dir=ROOT, suffix=".mp4") as video:
            video.write(b"video")
            video.flush()
            with (
                patch("timeline_mcp.server.UPLOAD_POST_API_KEY", "key"),
                patch("timeline_mcp.server.UPLOAD_POST_USER", "profile"),
                patch("timeline_mcp.server.requests.post", return_value=response) as post,
            ):
                result = publish_video(video.name.split("/")[-1])

        self.assertEqual(result["status"], "ok")
        self.assertEqual(post.call_args.kwargs["data"]["platform[]"], "instagram")
        self.assertEqual(post.call_args.kwargs["data"]["media_type"], "REELS")


if __name__ == "__main__":
    unittest.main()
