import openai
import os
import json
import uuid
import base64
import logging
from pathlib import Path
from models import DetailedAnalysis, EvaluationFeedback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('excel_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_SERVICE_ACCOUNT_KEY')

def fix_schema_for_openai_strict(schema):
    """Fix Pydantic schema for OpenAI strict mode by adding additionalProperties: false and making all properties required"""
    def fix_schema_recursive(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "object":
                obj["additionalProperties"] = False
                # For OpenAI strict mode, all properties must be required
                if "properties" in obj:
                    obj["required"] = list(obj["properties"].keys())
            for value in obj.values():
                fix_schema_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_schema_recursive(item)
    
    fix_schema_recursive(schema)
    return schema

def upload_excel_file():
    """Handle Excel file upload from user"""
    # logger.info("[UPLOAD] Starting file upload process")
    
    while True:
        file_path = input("\nPlease enter the path to your Excel file (or 'cancel' to go back): ").strip()
        # logger.info(f"[INPUT] User provided path: {file_path}")
        
        if file_path.lower() == 'cancel':
            # logger.info("[CANCEL] User cancelled file upload")
            return None
        
        try:
            # Convert to Path object and resolve
            file_path = Path(file_path)
            # logger.info(f"[CHECK] Checking file path: {file_path.absolute()}")
            
            # Check if file exists
            if not file_path.exists():
                # logger.warning(f"[ERROR] File not found: {file_path}")
                print("File not found. Please check the path and try again.")
                continue
            
            # Check if it's an Excel file
            if file_path.suffix.lower() not in ['.xlsx', '.xls', '.xlsm']:
                # logger.warning(f"[ERROR] Invalid file type: {file_path.suffix}")
                print("Please upload a valid Excel file (.xlsx, .xls, or .xlsm)")
                continue
            
            # logger.info(f"[READ] Reading file: {file_path.name}")
            
            # Read and encode the file
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
                encoded_file = base64.b64encode(file_bytes).decode('utf-8')
            
            file_size_kb = len(file_bytes) / 1024
            # logger.info(f"[SUCCESS] File uploaded successfully: {file_path.name} ({file_size_kb:.1f} KB)")
            print(f"File '{file_path.name}' uploaded successfully!")
            
            return {
                'filename': file_path.name,
                'encoded_data': encoded_file,
                'size_kb': file_size_kb
            }
            
        except PermissionError as e:
            # logger.error(f"[ERROR] Permission denied reading file: {e}")
            print("Permission denied. Please check if the file is open in another application.")
        except Exception as e:
            # logger.error(f"[ERROR] Error reading file: {e}")
            print(f"Error reading file: {str(e)}")

def detect_upload_intent(user_input):
    """Detect if user wants to upload a file"""
    upload_keywords = [
        'upload', 'submit', 'file', 'workbook', 'excel', 'spreadsheet', 
        'evaluate', 'check', 'review', 'assess', '.xlsx', '.xls'
    ]
    user_lower = user_input.lower()
    return any(keyword in user_lower for keyword in upload_keywords)

def evaluate_excel_with_llm(uploaded_file_data, task_id) -> dict:
    """Use LLM to evaluate the uploaded Excel file"""
    # logger.info(f"[EVAL] Starting LLM evaluation for file: {uploaded_file_data.get('filename')} (Task: {task_id})")
    
    evaluation_prompt = f"""You are an Excel evaluation expert. You need to analyze an uploaded Excel workbook and provide detailed feedback.

**Task Context:**
- Task ID: {task_id}
- Filename: {uploaded_file_data.get('filename')}
- File size: {uploaded_file_data.get('size_kb', 0):.1f} KB

**Your Role:**
Analyze this Excel workbook and evaluate the candidate's Excel skills based on:
1. **Technical Accuracy** (30 points): Correct formulas, calculations, data handling
2. **Pivot Tables & Analysis** (25 points): Proper use of pivot tables, data summarization
3. **Charts & Visualization** (20 points): Effective charts, proper formatting, clarity
4. **Data Organization** (15 points): Structure, layout, readability
5. **Advanced Features** (10 points): Use of advanced Excel functions, conditional formatting, etc.

**Instructions:**
1. Provide a numerical score out of 10 (scaled down from 100)
2. Give specific feedback on what was done well
3. Identify areas for improvement
4. Give actionable recommendations

**Note:** Since I cannot directly analyze the Excel file content, provide an evaluation framework and ask the candidate to describe what they implemented, or indicate that manual review is needed."""

    try:
        # logger.info("[API] Sending request to OpenAI API for evaluation")
        # logger.debug(f"[PROMPT] Evaluation prompt length: {len(evaluation_prompt)} characters")
        
        # Generate schema and fix for OpenAI strict mode
        schema = EvaluationFeedback.model_json_schema()
        schema = fix_schema_for_openai_strict(schema)
        # logger.debug(f"[SCHEMA] Fixed schema for OpenAI: {schema}")
        
        # Make the LLM call with fixed schema
        evaluation_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": evaluation_prompt},
                {"role": "user", "content": f"Please evaluate this Excel workbook. The file is base64 encoded but I need you to provide an evaluation framework. File data: {uploaded_file_data.get('filename')} ({uploaded_file_data.get('size_kb', 0):.1f} KB)"}
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "excel_evaluation",
                    "schema": schema,
                    "strict": True
                }
            }
        )
        
        # logger.info("[API] Received response from OpenAI API")
        # logger.debug(f"[USAGE] Response usage: {evaluation_response.usage}")
        
        # Parse response directly into Pydantic model
        raw_content = evaluation_response.choices[0].message.content
        # logger.info(f"[RESPONSE] Raw response length: {len(raw_content) if raw_content else 0} characters")
        # logger.debug(f"[CONTENT] Raw response content: {raw_content}")
        
        evaluation_data = json.loads(raw_content)
        # logger.info("[SUCCESS] Successfully parsed JSON response")
        # logger.debug(f"[DATA] Parsed data keys: {list(evaluation_data.keys())}")
        
        evaluation_result = EvaluationFeedback(**evaluation_data)
        # logger.info("[SUCCESS] Successfully created Pydantic model")
        # logger.info(f"[SCORE] Evaluation score: {evaluation_result.score}")
        
        # Return as dictionary for compatibility with existing code
        result = evaluation_result.model_dump()
        # logger.info("[SUCCESS] Evaluation completed successfully")
        return result
            
    except json.JSONDecodeError as e:
        # logger.error(f"[ERROR] JSON parsing error: {e}")
        # logger.error(f"[ERROR] Raw content that failed to parse: {raw_content}")
        error_evaluation = EvaluationFeedback(
            score=0,
            feedback=f"JSON parsing error in evaluation. Error: {str(e)}",
            recommendations=["Please try uploading the file again or contact support"]
        )
        return error_evaluation.model_dump()
    except Exception as e:
        # logger.error(f"[ERROR] Evaluation error: {e}")
        # logger.error(f"[ERROR] Error type: {type(e).__name__}")
        
        # Error handling - return structured error response using Pydantic
        error_evaluation = EvaluationFeedback(
            score=0,
            feedback=f"Unable to evaluate the workbook at this time. Error: {str(e)}",
            recommendations=["Please try uploading the file again or contact support"]
        )
        return error_evaluation.model_dump()

def llm_evaluate_excel(workbook_summary: str) -> dict:
    """Streamlined Excel evaluation using workbook summary"""
    # logger.info(f"[STREAMLINED] Starting streamlined evaluation with summary: {workbook_summary[:100]}...")
    
    system_prompt = (
        "You are a strict but fair Excel interviewer. Given the workbook summary, evaluate the candidate's effort. "
        "Respond in JSON with score (0–10), qualitative feedback, and action recommendations as a list of strings."
    )

    user_prompt = f"Workbook Summary:\n{workbook_summary}"

    try:
        # logger.info("[API] Sending streamlined evaluation request to OpenAI API")
        
        # Generate schema and fix for OpenAI strict mode
        schema = EvaluationFeedback.model_json_schema()
        schema = fix_schema_for_openai_strict(schema)
        # logger.debug(f"[SCHEMA] Fixed streamlined schema: {schema}")
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            top_p=0.8,
            seed=2223,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_feedback",
                    "schema": schema,
                    "strict": True
                }
            }
        )

        # logger.info("[API] Received streamlined evaluation response")
        raw_content = response.choices[0].message.content
        # logger.debug(f"[CONTENT] Streamlined response content: {raw_content}")
        
        result = json.loads(raw_content)
        # logger.info("[SUCCESS] Successfully parsed streamlined JSON response")
        
        feedback = EvaluationFeedback(**result)
        # logger.info(f"[SUCCESS] Streamlined evaluation completed with score: {feedback.score}")
        
        return feedback.model_dump()
    
    except json.JSONDecodeError as e:
        # logger.error(f"[ERROR] JSON parsing error in streamlined evaluation: {e}")
        error_feedback = EvaluationFeedback(
            score=0,
            feedback=f"JSON parsing error in streamlined evaluation. Error: {str(e)}",
            recommendations=["Please try again or contact support"]
        )
        return error_feedback.model_dump()
    except Exception as e:
        # logger.error(f"[ERROR] Streamlined evaluation error: {e}")
        # logger.error(f"[ERROR] Error type: {type(e).__name__}")
        
        # Error handling with structured response
        error_feedback = EvaluationFeedback(
            score=0,
            feedback=f"Unable to evaluate the workbook summary. Error: {str(e)}",
            recommendations=["Please try again or contact support"]
        )
        return error_feedback.model_dump()

def handle_tool_calls(tool_calls, uploaded_file_data=None):
    """Handle tool calls from OpenAI API"""
    # logger.info(f"[TOOLS] Handling {len(tool_calls)} tool call(s)")
    tool_results = []
    
    for i, tool_call in enumerate(tool_calls):
        function_name = tool_call.function.name
        # logger.info(f"[TOOL] Tool {i+1}/{len(tool_calls)}: {function_name}")
        # logger.debug(f"[ID] Tool call ID: {tool_call.id}")
        
        try:
            function_args = json.loads(tool_call.function.arguments)
            # logger.debug(f"[ARGS] Function arguments: {function_args}")
        except json.JSONDecodeError as e:
            # logger.error(f"[ERROR] Failed to parse tool arguments: {e}")
            continue
        
        # Import tool handlers
        from tool_handlers import TOOL_FUNCTIONS
        
        # Handle each tool function using the dedicated handlers
        if function_name in TOOL_FUNCTIONS:
            tool_func = TOOL_FUNCTIONS[function_name]
            
            try:
                if function_name == "start_excel_assessment":
                    result = tool_func(function_args.get("candidate_name"))
                elif function_name == "generate_excel_task":
                    result = tool_func(
                        function_args.get("session_id"),
                        function_args.get("question_number", 1)
                    )
                elif function_name == "next_excel_question":
                    result = tool_func(
                        function_args.get("session_id"),
                        function_args.get("current_question", 1)
                    )
                elif function_name == "evaluate_workbook":
                    result = tool_func(
                        function_args.get("session_id"),
                        function_args.get("task_id"),
                        uploaded_file_data
                    )
                elif function_name == "llm_evaluate_excel":
                    result = tool_func(function_args.get("workbook_summary"))
                elif function_name == "summarize_assessment":
                    result = tool_func(function_args.get("session_id"))
                else:
                    # logger.error(f"[ERROR] Unhandled function: {function_name}")
                    result = {"error": f"Unhandled function: {function_name}"}
                    
            except Exception as e:
                # logger.error(f"[ERROR] Tool function {function_name} failed: {e}")
                result = {"error": f"Tool function {function_name} failed: {str(e)}"}
        else:
            # logger.error(f"[ERROR] Unknown function called: {function_name}")
            result = {"error": f"Unknown function: {function_name}"}
        
        # Create proper tool response message format
        # logger.debug(f"[RESULT] Tool result keys: {list(result.keys())}")
        tool_response = {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        }
        tool_results.append(tool_response)
        # logger.info(f"[SUCCESS] Tool {function_name} completed successfully")
    
    # logger.info(f"[COMPLETE] All {len(tool_calls)} tool calls completed")
    return tool_results 