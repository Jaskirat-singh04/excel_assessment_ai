import uuid
import logging
from evaluation import evaluate_excel_with_llm, llm_evaluate_excel

logger = logging.getLogger(__name__)

def start_excel_assessment(candidate_name: str) -> dict:
    """Initialize session for Excel assessment"""
    logger.info("[TOOL] Executing start_excel_assessment")
    logger.info(f"[CANDIDATE] Starting assessment for candidate: {candidate_name}")
    
    session_id = str(uuid.uuid4())
    
    return {
        "session_id": session_id,
        "message": f"Hello {candidate_name}! I'm your Excel Interview Agent. Let's begin your Excel proficiency assessment.",
        "status": "assessment_started",
        "next_step": "I will now provide you with the Excel assessment tasks. You'll need to download a sample file to complete the exercises."
    }

def generate_excel_task(session_id: str, question_number: int = 1) -> dict:
    """Ask the next Excel assessment question"""
    logger.info("[TOOL] Executing generate_excel_task")
    logger.info(f"[SESSION] Session ID: {session_id}")
    logger.info(f"[QUESTION] Question number: {question_number}")
    
    task_id = str(uuid.uuid4())
    logger.info(f"[TASK] Generated task ID: {task_id}")
    
    # Define the 5 assessment questions
    questions = {
        1: {
            "title": "📥 Download Sample Data",
            "question": "First, let's get you set up with the sample data. Please download the file 'dummy_excel_assessment_data.xlsx' from the assessment directory. This file contains sales data that you'll use for all the Excel tasks. Have you successfully downloaded and opened the file?",
            "task": "Download and open the sample Excel file",
            "expected_response": "Confirmation that file is downloaded and opened"
        },
        2: {
            "title": "📊 Question 1: Basic Pivot Table",
            "question": "Great! Now let's start with your first Excel task. Create a pivot table that shows the total revenue by region. Place the 'Region' field in the Rows area and 'Revenue' in the Values area. Once you've created this pivot table, let me know what regions you see and which region has the highest revenue.",
            "task": "Create a basic pivot table showing revenue by region",
            "expected_response": "List of regions and identification of highest revenue region"
        },
        3: {
            "title": "📈 Question 2: Chart Creation",
            "question": "Excellent work on the pivot table! Now, let's add visualization. Create a bar chart based on your pivot table to show the revenue by region visually. After creating the chart, tell me: What type of chart did you choose and what insights can you gather from the visual representation of the data?",
            "task": "Add a bar chart to visualize the pivot table data",
            "expected_response": "Description of chart type and data insights"
        },
        4: {
            "title": "🔍 Question 3: Advanced Analysis", 
            "question": "Perfect! Now let's do some deeper analysis. Create a new pivot table that breaks down sales by both 'Product Category' and 'Region'. This should show you how different product categories perform in each region. What's the top-selling product category overall, and which region-product combination generates the most revenue?",
            "task": "Create advanced pivot table with Product Category and Region",
            "expected_response": "Top product category and best region-product combination"
        },
        5: {
            "title": "💡 Question 4: Calculated Fields",
            "question": "Great analysis! Now let's work with formulas. Add a new column called 'Profit Margin' that calculates the difference between Revenue and Cost (Revenue - Cost). Then apply conditional formatting to highlight profit margins above $1000 in green and below $500 in red. What's the average profit margin you calculated?",
            "task": "Add calculated column and conditional formatting",
            "expected_response": "Average profit margin value and confirmation of formatting"
        },
        6: {
            "title": "📋 Question 5: Final Task & Upload",
            "question": "Excellent work! For your final task, please save all your completed work in the Excel file. Make sure all your pivot tables, charts, and calculated fields are properly formatted and easy to read. Once everything is saved, please upload your completed Excel file. Type 'upload' when you're ready to submit your work for evaluation.",
            "task": "Save work and upload completed file",  
            "expected_response": "File upload with completed Excel tasks"
        }
    }
    
    # Get the current question or default to question 1
    current_question = questions.get(question_number, questions[1])
    
    return {
        "task_id": task_id,
        "session_id": session_id,
        "question_number": question_number,
        "total_questions": 5,
        "question_title": current_question["title"],
        "question": current_question["question"],
        "task": current_question["task"],
        "expected_response": current_question["expected_response"],
        "sample_file": "dummy_excel_assessment_data.xlsx" if question_number == 1 else None
    }

def evaluate_workbook(session_id: str, task_id: str, uploaded_file_data: dict = None) -> dict:
    """Evaluate the submitted Excel workbook"""
    logger.info("[TOOL] Executing evaluate_workbook")
    logger.info(f"[SESSION] Session ID: {session_id}")
    logger.info(f"[TASK] Task ID: {task_id}")
    
    if uploaded_file_data:
        logger.info(f"[FILE] Evaluating uploaded file: {uploaded_file_data.get('filename')}")
        
        # Use LLM to evaluate the Excel file
        evaluation_result = evaluate_excel_with_llm(uploaded_file_data, task_id)
        logger.info("[EVAL] Workbook evaluation completed")
        
        return {
            "session_id": session_id,
            "task_id": task_id,
            "filename": uploaded_file_data.get('filename'),
            **evaluation_result
        }
    else:
        logger.warning("[ERROR] No file data provided for workbook evaluation")
        return {
            "error": "No file uploaded. Please upload your Excel workbook first."
        }

def llm_evaluate_excel_tool(workbook_summary: str) -> dict:
    """Evaluate workbook using summary (streamlined evaluation)"""
    logger.info("[TOOL] Executing llm_evaluate_excel (streamlined)")
    logger.info(f"[SUMMARY] Summary length: {len(workbook_summary) if workbook_summary else 0} characters")
    
    # Use the streamlined evaluation function
    evaluation_result = llm_evaluate_excel(workbook_summary)
    logger.info("[SUCCESS] Streamlined evaluation tool completed")
    
    return {
        "evaluation_type": "streamlined",
        "workbook_summary": workbook_summary,
        **evaluation_result
    }

def summarize_assessment(session_id: str) -> dict:
    """Generate summary of Excel assessment and create PDF report"""
    logger.info("[TOOL] Executing summarize_assessment")
    logger.info(f"[SESSION] Session ID: {session_id}")
    
    # Get evaluation results from LLM
    evaluation = llm_evaluate_excel_tool({
        "session_id": session_id,
        "request_type": "final_summary" 
    })
    
    # Create PDF summary report
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    pdf_filename = f"excel_assessment_{session_id}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Add content to PDF
    story.append(Paragraph(f"Excel Assessment Summary - Session {session_id}", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Overall Score: {evaluation['score']}/10", styles['Heading2']))
    story.append(Paragraph(f"Grade: {evaluation['grade']}", styles['Heading2']))
    story.append(Paragraph(evaluation['summary'], styles['Normal']))
    
    # Build and save PDF
    doc.build(story)
    logger.info(f"[PDF] Generated summary report: {pdf_filename}")
    
    return {
        "session_id": session_id,
        "evaluation": evaluation,
        "pdf_report": pdf_filename,
        "summary_status": "complete"
    }

def next_excel_question(session_id: str, current_question: int = 1) -> dict:
    """Move to the next Excel assessment question"""
    logger.info("[TOOL] Moving to next Excel question")
    logger.info(f"[SESSION] Session ID: {session_id}")
    logger.info(f"[PROGRESS] Moving from question {current_question} to {current_question + 1}")
    
    next_question_num = current_question + 1
    
    if next_question_num > 6:  # We have 6 steps total (including download)
        return {
            "status": "assessment_complete",
            "message": "Congratulations! You've completed all the Excel assessment questions. Please upload your final Excel file for evaluation.",
            "next_action": "upload_file"
        }
    
    # Get the next question using generate_excel_task
    return generate_excel_task(session_id, next_question_num)

def provide_download_help() -> dict:
    """Provide help for downloading the sample Excel file"""
    logger.info("[TOOL] Providing download help")
    
    return {
        "help_type": "download_assistance",
        "message": """
📥 **DOWNLOAD INSTRUCTIONS:**

**File Name:** dummy_excel_assessment_data.xlsx
**Location:** Current assessment directory

**How to Download:**
1. The file should be available in the same folder as this assessment tool
2. Look for 'dummy_excel_assessment_data.xlsx' in your file explorer
3. If you can't find it, please let me know and I'll provide alternative instructions

**File Contents:**
- Sample sales data with multiple sheets
- Columns: Date, Region, Product, Revenue, Cost, Salesperson
- Ready-to-use data for all assessment tasks

**Next Steps:**
1. Download the file
2. Open it in Microsoft Excel
3. Complete the 5 assessment tasks
4. Save your work
5. Upload the completed file back to me

Need help finding the file? Just ask!
        """,
        "sample_file_name": "dummy_excel_assessment_data.xlsx"
    }

# Tool function mapping
TOOL_FUNCTIONS = {
    "start_excel_assessment": start_excel_assessment,
    "generate_excel_task": generate_excel_task,
    "next_excel_question": next_excel_question,
    "evaluate_workbook": evaluate_workbook,
    "llm_evaluate_excel": llm_evaluate_excel_tool,
    "summarize_assessment": summarize_assessment
} 