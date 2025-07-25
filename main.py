import openai
import os
import logging
from tools import tools
from evaluation import handle_tool_calls, upload_excel_file, detect_upload_intent

# Configure logging for main
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_SERVICE_ACCOUNT_KEY')

def main():
    """Main function to run the Excel Interview Agent"""
    logger.info("[STARTUP] Starting Excel Interview Agent")
    logger.info("[CONFIG] OpenAI API key configured: " + ("YES" if openai.api_key else "NO"))
    
    prompt = '''You are "Excel Interview Agent", an AI interviewer designed to assess a candidate's technical proficiency in Microsoft Excel. Your role is to simulate a structured, professional, and interactive interview experience.

## Personality & Tone:
- You are strict but professional.
- You provide clear instructions and keep the conversation focused on Excel.
- You never answer non-Excel questions.
- You are polite but avoid unnecessary small talk.

## Conversation Structure:
1. **Introduction**
   - Greet the candidate and ask for their name.
   - Introduce yourself as an Excel interviewer and explain the structure of the assessment.
   - Explain that you will guide them through 5 Excel tasks one by one, starting with downloading a sample file.
   - Emphasize that this is an interactive, step-by-step assessment where you'll ask one question at a time.

2. **Interview Flow**
   - After collecting the candidate's name, call the tool `start_excel_assessment` to greet them, then provide a welcoming response.
   - Start with question 1 by calling `generate_excel_task` with question_number=1 (download step).
   - Ask ONE question at a time and wait for the user's response before proceeding.
   - After the user responds to each question, call `next_excel_question` to move to the next question.
   - There are 6 total steps: Download file, 4 Excel tasks, and final upload.
   - Always acknowledge the user's response before moving to the next question.
   - When the candidate mentions uploading their final file, guide them to upload their workbook.

3. **Answer Evaluation**
   - Acknowledge each response positively and encourage the candidate.
   - IMPORTANT: When you see "[FILE UPLOADED: filename]" in a message, immediately call `evaluate_workbook` tool.
   - This is the main evaluation step - do this as soon as a file is uploaded.
   - Provide detailed feedback based on the evaluation results.

4. **State Awareness**
   - Keep track of how many questions have been asked (must be exactly 5).
   - Ensure questions are not repeated.
   - Avoid re-asking the user's name or already answered questions.

5. **Final Summary** (only if needed)
   - After evaluating the uploaded file, you can optionally use `summarize_assessment` for additional summary.
   - But the main evaluation should always be done with `evaluate_workbook` first.

## Rules:
- Never fabricate questions — always use function tools for asking questions.
- If a candidate refuses or asks for a break, acknowledge politely and pause.
- Never break character or reveal that you are an AI language model.
- Never answer general queries unrelated to the Excel interview.
- Do not evaluate answers until all 5 questions are completed.
- When a candidate wants to upload their work, guide them through the file upload process.

## Objective:
The ultimate goal is to conduct a thorough assessment of Excel proficiency through 5 targeted questions, covering areas like formulas, pivot tables, functions (VLOOKUP, INDEX-MATCH), charting, and data analysis techniques, with comprehensive evaluation at the end.'''

    conversation_history = []
    conversation_history.append({"role": "system", "content": prompt})
    logger.info(f"[PROMPT] System prompt configured ({len(prompt)} characters)")

    print("=== Excel Interview Agent ===")
    print("Welcome! I can help assess your Excel skills.")
    print("You can upload Excel files by typing 'upload' or mentioning file upload.\n")
    logger.info("[READY] Agent ready for user interaction")

    while True:
        user_query = input("Enter your query: ")
        logger.info(f"[USER] User input: {user_query}")
        
        # Check if user wants to upload a file
        if detect_upload_intent(user_query):
            logger.info("[UPLOAD] Upload intent detected")
            print("\n📎 It looks like you want to upload an Excel file!")
            uploaded_file = upload_excel_file()
            
            if uploaded_file:
                # Modify the user query to indicate file upload
                user_query += f" [FILE UPLOADED: {uploaded_file['filename']}]"
                logger.info(f"[FILE] File uploaded: {uploaded_file['filename']} ({uploaded_file['size_kb']:.1f} KB)")
                print(f"Continuing with your uploaded file: {uploaded_file['filename']}")
            else:
                logger.info("[CANCEL] File upload cancelled")
                print("Upload cancelled. You can try again anytime.")
                continue
        else:
            uploaded_file = None
        
        conversation_history.append({"role": "user", "content": user_query})
        logger.info(f"[HISTORY] Conversation history length: {len(conversation_history)}")

        logger.info("[API] Sending request to OpenAI Chat API")
        response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation_history,
                    temperature=0,
                    tools=tools,
                    tool_choice="auto",
                    top_p=0.8,
                    seed=2223
                )
        
        msg = response.choices[0].message
        logger.info("[API] Received response from OpenAI Chat API")
        
        # Handle tool calls if present
        if msg.tool_calls:
            logger.info(f"[TOOLS] Tool calls detected: {len(msg.tool_calls)} tool(s)")
            print("AI: Processing...")
            
            # Add assistant message with tool calls to history
            conversation_history.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in msg.tool_calls
                ]
            })
            
            tool_results = handle_tool_calls(msg.tool_calls, uploaded_file)
            conversation_history.extend(tool_results)
            logger.info("[TOOLS] Tool results added to conversation history")
            
            # Get the follow-up response after tool execution
            logger.info("[API] Sending follow-up request to OpenAI API")
            follow_up_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history,
                temperature=0,
                tools=tools,
                tool_choice="auto",
                top_p=0.8,
                seed=2223
            )
            
            follow_up_msg = follow_up_response.choices[0].message
            logger.info("[API] Received follow-up response")
            
            # Check if the follow-up response also has tool calls
            if follow_up_msg.tool_calls:
                logger.info(f"[TOOLS] Follow-up response has {len(follow_up_msg.tool_calls)} more tool calls")
                # Add this assistant message with tool calls
                conversation_history.append({
                    "role": "assistant",
                    "content": follow_up_msg.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in follow_up_msg.tool_calls
                    ]
                })
                
                # Handle the additional tool calls
                additional_tool_results = handle_tool_calls(follow_up_msg.tool_calls, uploaded_file)
                conversation_history.extend(additional_tool_results)
                
                # Get final response after additional tools
                logger.info("[API] Sending final request after additional tools")
                final_response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation_history,
                    temperature=0,
                    tools=tools,
                    tool_choice="auto",
                    top_p=0.8,
                    seed=2223
                )
                
                final_msg = final_response.choices[0].message
                logger.info("[API] Received final response")
                conversation_history.append({
                    "role": "assistant",
                    "content": final_msg.content
                })
                
                if final_msg.content:
                    logger.info(f"[RESPONSE] Final AI response: {final_msg.content[:100]}...")
                    print("AI:", final_msg.content)
                else:
                    logger.warning("[WARNING] Final AI response has no content")
                    print("AI: (No response)")
            else:
                # Regular follow-up response without tool calls
                conversation_history.append({
                    "role": "assistant",
                    "content": follow_up_msg.content
                })
                
                if follow_up_msg.content:
                    logger.info(f"[RESPONSE] AI response: {follow_up_msg.content[:100]}...")
                    print("AI:", follow_up_msg.content)
                else:
                    # logger.warning("[WARNING] AI returned no content")
                    # logger.debug(f"[DEBUG] Follow-up message object: {follow_up_msg}")
                    # logger.debug(f"[DEBUG] Message content: '{follow_up_msg.content}'")
                    # logger.debug(f"[DEBUG] Message role: {follow_up_msg.role}")
                    # logger.debug(f"[DEBUG] Has tool calls: {bool(follow_up_msg.tool_calls)}")
                    # logger.debug(f"[DEBUG] Conversation history length: {len(conversation_history)}")
                    print("AI: (No response)")
        else:
            logger.info("[RESPONSE] Regular message (no tool calls)")
            # No tool calls, add regular message to history
            conversation_history.append({
                "role": "assistant",
                "content": msg.content
            })
            if msg.content:
                logger.info(f"[RESPONSE] AI response: {msg.content[:100]}...")
                print("AI:", msg.content)
            else:
                logger.warning("[WARNING] AI returned no content")
                print("AI: (No response)")

if __name__ == "__main__":
    main() 