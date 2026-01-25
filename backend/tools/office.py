from typing import Dict, Any, List
from .base import BaseTool
import io
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("robovai.tools.office")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from ics import Calendar, Event
    import pytz
    ICS_AVAILABLE = True
except ImportError:
    ICS_AVAILABLE = False

class ExcelAnalyzerTool(BaseTool):
    @property
    def name(self) -> str:
        return "/analyze_excel"

    @property
    def description(self) -> str:
        return "Analyzes Excel/CSV files and provides statistical summaries."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str, file_content: bytes = None, filename: str = "") -> Dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return {"status": "error", "output": "⚠️ Missing dependency: pandas. Please install it."}
        
        if not file_content:
             return {"status": "error", "output": "❌ No file provided."}

        try:
            # Determine Loader
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            # Analysis
            rows, cols = df.shape
            columns = list(df.columns)
            
            # Numeric Summary
            numeric_desc = df.describe().to_string()
            
            # Message Construction
            summary = f"""📊 **Excel Analysis Report**
            
**File**: `{filename}`
**Dimensions**: {rows} Rows × {cols} Columns
**Columns**: {', '.join(columns[:10])} {'...' if len(columns)>10 else ''}

**📈 Statistical Summary (Numeric):**
```
{numeric_desc}
```

**💡 Quick Insights:**
- Missing Values: {df.isnull().sum().sum()}
- Duplicates: {df.duplicated().sum()}
"""
            return {
                "status": "success",
                "output": summary,
                "tokens_deducted": 0
            }
        except Exception as e:
            return {"status": "error", "output": f"❌ Analysis Failed: {str(e)}"}

class CalendarEventTool(BaseTool):
    @property
    def name(self) -> str:
        return "/create_event"

    @property
    def description(self) -> str:
        return "Creates an .ics calendar file for meetings."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Input format: "Meeting title | 2025-10-20 14:00 | 2025-10-20 15:00"
        Or simplified: "Meeting title | 2025-10-20 14:00" (default 1h compatibility)
        """
        if not ICS_AVAILABLE:
             return {"status": "error", "output": "⚠️ Missing dependency: ics. Please install it."}

        parts = [p.strip() for p in user_input.split('|')]
        if len(parts) < 2:
             return {"status": "error", "output": "❌ Format: Title | Start Time (YYYY-MM-DD HH:MM) | [End Time]"}

        title = parts[0]
        start_str = parts[1]
        
        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            if len(parts) > 2:
                end_time = datetime.strptime(parts[2], "%Y-%m-%d %H:%M")
            else:
                end_time = start_time + timedelta(hours=1)
            
            c = Calendar()
            e = Event()
            e.name = title
            e.begin = start_time
            e.end = end_time
            c.events.add(e)
            
            # We return the content string; the bot handler should save to file and send
            return {
                "status": "success",
                "output": f"📅 **Event Created:** {title}\nTime: {start_time}",
                "file_content": str(c),
                "file_name": "invite.ics",
                "tokens_deducted": 0
            }

        except ValueError:
             return {"status": "error", "output": "❌ Invalid Date Format. Use YYYY-MM-DD HH:MM"}
