"""
📺 YouTube Tool - Video Analysis & Transcript
"""

from backend.tools.base import BaseTool
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
import logging

# Try to import youtube_transcript_api, handle missing dependency
try:
    from youtube_transcript_api import YouTubeTranscriptApi

    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False

logger = logging.getLogger("robovai.tools.youtube")


class YouTubeSchema(BaseModel):
    video_url: str = Field(..., description="The YouTube video URL or ID")
    language: str = Field(
        "en", description="Language code for transcript (e.g., 'en', 'ar')"
    )


class YouTubeTool(BaseTool):
    """
    Get transcript and info from YouTube videos.
    """

    @property
    def name(self) -> str:
        return "/youtube_transcript"

    @property
    def description(self) -> str:
        return "Extract transcript/captions from a YouTube video."

    @property
    def cost(self) -> int:
        return 2

    @property
    def args_schema(self) -> Type[BaseModel]:
        return YouTubeSchema

    async def execute_kwargs(
        self, user_id: str, video_url: str, language: str = "en"
    ) -> Dict[str, Any]:
        if not HAS_YOUTUBE:
            return {
                "status": "error",
                "output": "❌ YouTube Transcript API not installed. Please install 'youtube-transcript-api'.",
            }

        try:
            # Extract video ID
            import re

            video_id = ""
            if "v=" in video_url:
                video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be" in video_url:
                video_id = video_url.split("/")[-1]
            else:
                video_id = video_url  # Assume ID given

            if not video_id:
                return {"status": "error", "output": "Invalid YouTube URL"}

            # Get transcript
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[language, "en"]
                )
            except Exception:
                # Fallback to auto-generated
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            full_text = " ".join([t["text"] for t in transcript_list])

            return {
                "status": "success",
                "output": full_text[:10000] + ("..." if len(full_text) > 10000 else ""),
                "full_text_length": len(full_text),
            }

        except Exception as e:
            return {"status": "error", "output": f"Failed to get transcript: {str(e)}"}

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Legacy execution"""
        return await self.execute_kwargs(user_id, video_url=user_input)
