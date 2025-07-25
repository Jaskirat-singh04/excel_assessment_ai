from typing import Dict, Any

tools = [
    {
        "type": "function",
        "function": {
            "name": "start_excel_assessment",
            "description": "Initialize session for Excel assessment",
            "parameters": {
                "type": "object",
                "properties": {"candidate_name": {"type": "string"}},
                "required": ["candidate_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_excel_task",
            "description": "Assign next Excel task to candidate",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "question_number": {"type": "integer", "description": "Current question number (1-6)"}
                },
                "required": ["session_id"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "next_excel_question",
            "description": "Move to the next Excel assessment question",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "current_question": {"type": "integer", "description": "Current question number"}
                },
                "required": ["session_id", "current_question"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_workbook",
            "description": "Evaluate the submitted Excel workbook",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "task_id": {"type": "string"},
                    "workbook_bytes": {"type": "string","description": "base64-encoded Excel file"}
                },
                "required": ["session_id", "task_id", "workbook_bytes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_assessment",
            "description": "Generate summary of Excel assessment",
            "parameters": {
                "type": "object",
                "properties": {"session_id": {"type": "string"}},
                "required": ["session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "llm_evaluate_excel",
            "description": "Evaluate the user's submitted Excel workbook, provide score, feedback, and recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "workbook_summary": {
                        "type": "string",
                        "description": "A short JSON-style summary of the Excel workbook's pivot tables, charts, and regions"
                    }
                },
                "required": ["workbook_summary"],
                "additionalProperties": False
            }
        }
    }
]