import streamlit as st
import openai
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import base64

# Import our backend modules
from tool_handlers import TOOL_FUNCTIONS
from evaluation import handle_tool_calls, upload_excel_file, detect_upload_intent
from models import EvaluationFeedback

# Configure page
st.set_page_config(
    page_title="Excel Interview Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_SERVICE_ACCOUNT_KEY')

# System prompt
SYSTEM_PROMPT = '''You are "Excel Interview Agent", an AI interviewer designed to assess a candidate's technical proficiency in Microsoft Excel. Your role is to simulate a structured, professional, and interactive interview experience.

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
   - Keep track of the interview stage: intro, Q&A in progress, wrap-up.
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
- When a candidate wants to upload their work, guide them through the file upload process.

## Objective:
The ultimate goal is to reduce human interviewer effort while maintaining high-quality assessments of Excel proficiency in areas like formulas, pivot tables, functions (VLOOKUP, INDEX-MATCH), charting, and data analysis techniques.'''

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'assessment_started' not in st.session_state:
        st.session_state.assessment_started = False
    if 'uploaded_file_data' not in st.session_state:
        st.session_state.uploaded_file_data = None

def call_openai_api(messages, tools=None):
    """Call OpenAI API with error handling"""
    try:
        from tools import tools as available_tools
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            tools=available_tools if tools is None else tools,
            tool_choice="auto",
            top_p=0.8,
            seed=2223
        )
        return response
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

def handle_file_upload():
    """Handle Excel file upload in Streamlit"""
    uploaded_file = st.file_uploader(
        "📁 Upload your completed Excel file",
        type=['xlsx', 'xls', 'xlsm'],
        help="Upload your completed Excel assessment file"
    )
    
    if uploaded_file is not None:
        # Convert uploaded file to base64
        file_bytes = uploaded_file.read()
        encoded_file = base64.b64encode(file_bytes).decode('utf-8')
        
        file_data = {
            'filename': uploaded_file.name,
            'encoded_data': encoded_file,
            'size_kb': len(file_bytes) / 1024
        }
        
        # Check if this is a new file upload
        if st.session_state.uploaded_file_data is None or st.session_state.uploaded_file_data.get('filename') != uploaded_file.name:
            st.session_state.uploaded_file_data = file_data
            st.success(f"✅ File '{uploaded_file.name}' uploaded successfully! ({file_data['size_kb']:.1f} KB)")
            
            # Automatically trigger evaluation
            evaluation_message = f"I have uploaded my Excel file: {uploaded_file.name}. Please evaluate my work."
            st.session_state.messages.append({"role": "user", "content": evaluation_message})
            st.session_state.conversation_history.append({"role": "user", "content": evaluation_message + f" [FILE UPLOADED: {uploaded_file.name}]"})
            st.rerun()
        
        return file_data
    
    return None

def download_sample_file():
    """Provide download link for sample Excel file"""
    sample_file_path = Path("dummy_excel_assessment_data.xlsx")
    
    if sample_file_path.exists():
        with open(sample_file_path, "rb") as file:
            btn = st.download_button(
                label="📥 Download Sample Excel File",
                data=file.read(),
                file_name="dummy_excel_assessment_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download this file to complete your Excel assessment tasks"
            )
            return btn
    else:
        st.warning("⚠️ Sample file 'dummy_excel_assessment_data.xlsx' not found in the current directory.")
        return False

def display_evaluation_results(tool_results):
    """Display evaluation results with scoring breakdown"""
    for result in tool_results:
        if result.get("role") == "tool" and "score" in result.get("content", ""):
            try:
                # Parse the tool result content
                import json
                result_data = json.loads(result["content"])
                
                if "score" in result_data:
                    st.success("🎉 **Evaluation Complete!**")
                    
                    # Overall Score
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("📊 **Overall Score**", f"{result_data.get('score', 0)}/100")
                    
                    with col2:
                        # Score interpretation
                        score = result_data.get('score', 0)
                        if score >= 90:
                            st.success("🏆 **Expert Level** - Outstanding Excel proficiency!")
                        elif score >= 80:
                            st.success("⭐ **Proficient** - Strong Excel skills!")
                        elif score >= 70:
                            st.info("👍 **Competent** - Good foundation with room for improvement")
                        elif score >= 60:
                            st.warning("📈 **Basic** - Developing Excel skills")
                        else:
                            st.error("📚 **Needs Training** - Significant skill development required")
                    
                    # Detailed Breakdown
                    st.subheader("📊 **Detailed Score Breakdown**")
                    
                    # Create columns for scoring categories
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        tech_score = result_data.get('technical_accuracy', 0)
                        st.metric("🔧 Technical Accuracy", f"{tech_score}/30")
                        st.progress(tech_score / 30)
                        
                        pivot_score = result_data.get('pivot_tables', 0)
                        st.metric("📊 Pivot Tables", f"{pivot_score}/25")
                        st.progress(pivot_score / 25)
                    
                    with col2:
                        viz_score = result_data.get('visualization', 0)
                        st.metric("📈 Visualization", f"{viz_score}/20")
                        st.progress(viz_score / 20)
                        
                        org_score = result_data.get('data_organization', 0)
                        st.metric("📋 Data Organization", f"{org_score}/15")
                        st.progress(org_score / 15)
                    
                    with col3:
                        pres_score = result_data.get('presentation', 0)
                        st.metric("✨ Presentation", f"{pres_score}/10")
                        st.progress(pres_score / 10)
                    
                    # Feedback and Recommendations
                    if result_data.get('feedback'):
                        st.subheader("💬 **Detailed Feedback**")
                        st.write(result_data['feedback'])
                    
                    if result_data.get('recommendations'):
                        st.subheader("🎯 **Recommendations for Improvement**")
                        for i, rec in enumerate(result_data['recommendations'], 1):
                            st.write(f"**{i}.** {rec}")
                    
                    return True
            
            except (json.JSONDecodeError, KeyError):
                continue
    
    return False

def display_progress():
    """Display assessment progress"""
    if st.session_state.current_question > 0:
        progress = min(st.session_state.current_question / 6, 1.0)
        st.progress(progress)
        st.write(f"📊 Progress: Question {st.session_state.current_question} of 6")
        
        # Progress steps
        steps = [
            "📥 Download Sample File",
            "📊 Basic Pivot Table", 
            "📈 Create Chart",
            "🔍 Advanced Analysis",
            "💡 Calculated Fields",
            "📤 Upload & Review"
        ]
        
        for i, step in enumerate(steps, 1):
            if i < st.session_state.current_question:
                st.write(f"✅ {step}")
            elif i == st.session_state.current_question:
                st.write(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")

def main():
    """Main Streamlit app"""
    initialize_session_state()
    
    # Header
    st.title("📊 Excel Interview Agent")
    st.markdown("### AI-Powered Excel Proficiency Assessment")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Assessment Info")
        st.write(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        
        # Progress tracking
        display_progress()
        
        # Sample file download
        st.header("📥 Sample File")
        if download_sample_file():
            st.success("Click to download the sample Excel file for your assessment tasks.")
        
        # File upload section
        st.header("📤 File Upload")
        uploaded_file_data = handle_file_upload()
        
        # Show upload status
        if st.session_state.uploaded_file_data:
            st.success(f"✅ File Ready: {st.session_state.uploaded_file_data['filename']}")
        else:
            st.info("📁 No file uploaded yet")
        
        # Assessment status
        st.header("📈 Status")
        if st.session_state.assessment_started:
            st.success("✅ Assessment in progress")
        else:
            st.info("🔄 Ready to start assessment")
        
        # Reset button
        st.header("🔄 Session Control")
        if st.button("🔄 Reset Assessment", help="Start a new assessment session"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Quick start guide
        st.header("💡 Quick Start")
        st.markdown("""
        **Getting Started:**
        1. Type your name to begin
        2. Download the sample Excel file
        3. Complete each Excel task
        4. Upload your completed work  
        5. Receive detailed feedback
        """)
        
        # Tips
        with st.expander("💡 Assessment Tips"):
            st.markdown("""
            **Excel Tasks Include:**
            - Creating pivot tables
            - Building charts and visualizations
            - Using formulas and functions
            - Data analysis and formatting
            - Professional presentation
            
            **Best Practices:**
            - Follow instructions carefully
            - Ask questions if unclear
            - Save your work frequently
            - Upload the completed file when done
            """)
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process the message
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Check if user wants to upload file and add file info if available
                if detect_upload_intent(prompt) and st.session_state.uploaded_file_data:
                    prompt += f" [FILE UPLOADED: {st.session_state.uploaded_file_data['filename']}]"
                
                # Call OpenAI API
                response = call_openai_api(st.session_state.conversation_history)
                
                if response:
                    msg = response.choices[0].message
                    
                    # Handle tool calls
                    if msg.tool_calls:
                        st.info("🔧 Processing your request...")
                        
                        # Add assistant message with tool calls to history
                        st.session_state.conversation_history.append({
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
                        
                        # Handle tool calls
                        tool_results = handle_tool_calls(msg.tool_calls, st.session_state.uploaded_file_data)
                        st.session_state.conversation_history.extend(tool_results)
                        
                        # Display evaluation results if available
                        if display_evaluation_results(tool_results):
                            st.markdown("---")
                        
                        # Get follow-up response
                        follow_up_response = call_openai_api(st.session_state.conversation_history)
                        
                        if follow_up_response:
                            follow_up_msg = follow_up_response.choices[0].message
                            
                            # Handle nested tool calls if any
                            if follow_up_msg.tool_calls:
                                st.session_state.conversation_history.append({
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
                                
                                additional_tool_results = handle_tool_calls(follow_up_msg.tool_calls, st.session_state.uploaded_file_data)
                                st.session_state.conversation_history.extend(additional_tool_results)
                                
                                # Display evaluation results if available
                                if display_evaluation_results(additional_tool_results):
                                    st.markdown("---")
                                
                                # Get final response
                                final_response = call_openai_api(st.session_state.conversation_history)
                                if final_response:
                                    final_msg = final_response.choices[0].message
                                    st.session_state.conversation_history.append({
                                        "role": "assistant",
                                        "content": final_msg.content
                                    })
                                    
                                    if final_msg.content:
                                        st.markdown(final_msg.content)
                                        st.session_state.messages.append({"role": "assistant", "content": final_msg.content})
                                    else:
                                        st.error("No response received from the assistant.")
                            else:
                                # Regular follow-up response
                                st.session_state.conversation_history.append({
                                    "role": "assistant",
                                    "content": follow_up_msg.content
                                })
                                
                                if follow_up_msg.content:
                                    st.markdown(follow_up_msg.content)
                                    st.session_state.messages.append({"role": "assistant", "content": follow_up_msg.content})
                                else:
                                    st.error("No response received from the assistant.")
                    else:
                        # Regular message without tool calls
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "content": msg.content
                        })
                        
                        if msg.content:
                            st.markdown(msg.content)
                            st.session_state.messages.append({"role": "assistant", "content": msg.content})
                        else:
                            st.error("No response received from the assistant.")
                else:
                    st.error("Failed to get response from the AI assistant.")
        
        # Update assessment status
        if not st.session_state.assessment_started and len(st.session_state.messages) > 0:
            st.session_state.assessment_started = True
        
        # Auto-rerun to update the interface
        st.rerun()

if __name__ == "__main__":
    main() 