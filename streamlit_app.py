import streamlit as st
import pandas as pd
import csv
import os
import random
from datetime import datetime
import io

class QuizManager:
    def __init__(self):
        self.quizzes = {}
        self.history = []
        self.current_stats = {
            'total_questions': 0,
            'correct_answers': 0,
            'chapter_stats': {},
            'missed_questions': []
        }
    
    def load_csv(self, filename, file_content=None):
        """Load quiz questions from CSV file or uploaded content"""
        try:
            if file_content is not None:
                # Use uploaded file content
                content = file_content.getvalue().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
            else:
                # Use file from disk
                if not os.path.exists(filename):
                    return False, "File not found. Please check the filename."
                
                with open(filename, 'r', encoding='utf-8') as file:
                    if os.path.getsize(filename) == 0:
                        return False, "CSV file is empty."
                    
                    reader = csv.DictReader(file)
            
            # Check required columns
            required_columns = ['Chapter', 'Question Text', 'Reasoning', 
                              'Correct_Answer', 'Alternative_1', 
                              'Alternative_2', 'Alternative_3']
            
            if not all(col in reader.fieldnames for col in required_columns):
                return False, f"CSV missing required columns. Found: {list(reader.fieldnames)}"
            
            questions = []
            line_number = 2
            
            for row in reader:
                if not any(row.values()):
                    continue
                
                # Validate required fields
                missing_fields = []
                for field in required_columns:
                    if not row.get(field) or str(row[field]).strip() == '':
                        missing_fields.append(field)
                
                if missing_fields:
                    line_number += 1
                    continue
                
                # Create question dictionary
                question = {
                    'chapter': row['Chapter'].strip(),
                    'question_text': row['Question Text'].strip(),
                    'reasoning': row['Reasoning'].strip(),
                    'correct_answer': row['Correct_Answer'].strip(),
                    'alternatives': [
                        row['Alternative_1'].strip(),
                        row['Alternative_2'].strip(),
                        row['Alternative_3'].strip()
                    ]
                }
                
                questions.append(question)
                line_number += 1
            
            if not questions:
                return False, "No valid questions found in CSV file."
            
            # Organize questions by chapter
            chapter_questions = {}
            for question in questions:
                chapter = question['chapter']
                if chapter not in chapter_questions:
                    chapter_questions[chapter] = []
                chapter_questions[chapter].append(question)
            
            return True, chapter_questions
            
        except Exception as e:
            return False, f"Error loading CSV: {str(e)}"

def start_quiz(self, class_name, selected_chapters, num_questions, chapter_questions):
    """Start the quiz session with selected chapters and number of questions"""
    # Reset current stats
    self.current_stats = {
        'total_questions': 0,
        'correct_answers': 0,
        'chapter_stats': {},
        'missed_questions': [],
        'class_name': class_name,
        'start_time': datetime.now(),
        'selected_chapters': selected_chapters
    }
    
    # Collect all questions from selected chapters
    all_questions = []
    for chapter in selected_chapters:
        if chapter in chapter_questions:
            all_questions.extend(chapter_questions[chapter])
    
    if not all_questions:
        return False, "No questions available for selected chapters."
    
    # Shuffle and select the requested number of questions
    random.shuffle(all_questions)
    selected_questions = all_questions[:min(num_questions, len(all_questions))]
    
    return True, selected_questions

    def submit_answer(self, question, user_answer, question_number):
        """Process a single answer and update statistics"""
        is_correct = user_answer == question['correct_answer']
        
        # Update statistics
        self.current_stats['total_questions'] += 1
        if is_correct:
            self.current_stats['correct_answers'] += 1
        else:
            missed_q = question.copy()
            missed_q['user_answer'] = user_answer
            missed_q['question_number'] = question_number
            self.current_stats['missed_questions'].append(missed_q)
        
        # Update chapter stats
        chapter = question['chapter']
        if chapter not in self.current_stats['chapter_stats']:
            self.current_stats['chapter_stats'][chapter] = {'asked': 0, 'correct': 0}
        
        self.current_stats['chapter_stats'][chapter]['asked'] += 1
        if is_correct:
            self.current_stats['chapter_stats'][chapter]['correct'] += 1
        
        return is_correct

    def save_quiz_session(self):
        """Save quiz session to history"""
        if self.current_stats['total_questions'] > 0:
            session_data = {
                'timestamp': datetime.now(),
                'class_name': self.current_stats['class_name'],
                'total_questions': self.current_stats['total_questions'],
                'correct_answers': self.current_stats['correct_answers'],
                'percentage': (self.current_stats['correct_answers'] / self.current_stats['total_questions'] * 100),
                'missed_questions': len(self.current_stats['missed_questions']),
                'chapter_stats': self.current_stats['chapter_stats'].copy(),
                'selected_chapters': self.current_stats.get('selected_chapters', [])
            }
            
            self.history.append(session_data)
            return True
        return False

    def get_history_df(self):
        """Return history as DataFrame for display and export"""
        if not self.history:
            return pd.DataFrame()
        
        history_data = []
        for session in self.history:
            history_data.append({
                'Date': session['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'Class': session['class_name'],
                'Total Questions': session['total_questions'],
                'Correct Answers': session['correct_answers'],
                'Percentage': f"{session['percentage']:.1f}%",
                'Missed Questions': session['missed_questions'],
                'Chapters': ', '.join(session.get('selected_chapters', []))
            })
        
        return pd.DataFrame(history_data)

    def get_questions_df(self, chapter_questions):
        """Return all questions as DataFrame for display"""
        all_questions = []
        for chapter, questions in chapter_questions.items():
            for q in questions:
                all_questions.append({
                    'Chapter': q['chapter'],
                    'Question': q['question_text'],
                    'Correct Answer': q['correct_answer'],
                    'Alternative 1': q['alternatives'][0],
                    'Alternative 2': q['alternatives'][1],
                    'Alternative 3': q['alternatives'][2],
                    'Reasoning': q['reasoning']
                })
        
        return pd.DataFrame(all_questions)

def main():
    # ... existing initialization code ...
    
    # Add quiz_results to session state
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    # ... rest of main function remains the same ...

def take_quiz(quiz_manager):
    st.header("🎯 Take Quiz")
    
    # Check if we should show results from a completed quiz
    if st.session_state.show_results and quiz_manager.current_stats['total_questions'] > 0:
        display_quiz_results(quiz_manager)
        
        if st.button("Start New Quiz"):
            st.session_state.show_results = False
            st.rerun()
        return
    
    if not quiz_manager.quizzes:
        st.warning("Please load a quiz set first from the 'Load Quiz Set' page.")
        return
    
    # ... existing quiz setup code remains the same ...
    
    # Display current quiz if in progress
    if st.session_state.quiz_started and st.session_state.current_quiz:
        display_quiz_question(quiz_manager)

def display_quiz_question(quiz_manager):
    questions = st.session_state.current_quiz
    current_idx = st.session_state.current_question
    
    if current_idx >= len(questions):
        return
    
    question = questions[current_idx]
    
    st.markdown("---")
    st.subheader(f"Question {current_idx + 1} of {len(questions)}")
    st.write(f"**Chapter:** {question['chapter']}")
    st.write(f"**Question:** {question['question_text']}")
    
    # Prepare options
    options = question['alternatives'] + [question['correct_answer']]
    random.shuffle(options)
    
    # Store the mapping for answer checking
    if 'option_mapping' not in st.session_state:
        st.session_state.option_mapping = {}
    st.session_state.option_mapping[current_idx] = options
    
    # Display options as radio buttons
    user_answer = st.radio(
        "Select your answer:",
        options,
        key=f"question_{current_idx}"
    )
    
    st.session_state.user_answers[current_idx] = user_answer
    
    col1, col2 = st.columns(2)
    
    with col1:
        if current_idx > 0:
            if st.button("← Previous Question"):
                st.session_state.current_question -= 1
                st.rerun()
    
    with col2:
        if current_idx < len(questions) - 1:
            if st.button("Next Question →"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("Submit Quiz", type="primary"):
                # Process all answers
                for i, (q, answer) in enumerate(zip(questions, st.session_state.user_answers)):
                    if answer is not None:
                        quiz_manager.submit_answer(q, answer, i + 1)
                
                st.session_state.quiz_completed = True
                st.session_state.quiz_started = False
                st.session_state.show_results = True
                quiz_manager.save_quiz_session()
                st.rerun()

    # Show progress
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.write(f"Progress: {current_idx + 1}/{len(questions)} questions")

def display_quiz_results(quiz_manager):
    """Display detailed quiz results after completion"""
    st.header("📊 Quiz Results")
    
    if not quiz_manager.current_stats or quiz_manager.current_stats['total_questions'] == 0:
        st.warning("No quiz results available.")
        return
    
    stats = quiz_manager.current_stats
    
    # Calculate overall score
    total_questions = stats['total_questions']
    correct_answers = stats['correct_answers']
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Display overall results with metrics
    st.subheader("📈 Overall Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Questions", total_questions)
    
    with col2:
        st.metric("Correct Answers", correct_answers)
    
    with col3:
        st.metric("Score", f"{percentage:.1f}%")
    
    with col4:
        st.metric("Missed Questions", len(stats['missed_questions']))
    
    # Progress bar for visualization
    st.progress(percentage / 100)
    
    # Grade interpretation
    if percentage >= 90:
        st.success(f"🎉 Excellent! You scored {percentage:.1f}%")
    elif percentage >= 80:
        st.success(f"👍 Very Good! You scored {percentage:.1f}%")
    elif percentage >= 70:
        st.info(f"😊 Good job! You scored {percentage:.1f}%")
    elif percentage >= 60:
        st.warning(f"📚 Keep practicing! You scored {percentage:.1f}%")
    else:
        st.error(f"📖 Review needed! You scored {percentage:.1f}%")
    
    # Display chapter-by-chapter performance
    st.subheader("📚 Chapter Performance")
    
    if stats['chapter_stats']:
        chapter_data = []
        for chapter, chapter_stat in stats['chapter_stats'].items():
            chapter_correct = chapter_stat['correct']
            chapter_asked = chapter_stat['asked']
            chapter_percentage = (chapter_correct / chapter_asked * 100) if chapter_asked > 0 else 0
            
            chapter_data.append({
                'Chapter': chapter,
                'Questions': chapter_asked,
                'Correct': chapter_correct,
                'Score': f"{chapter_percentage:.1f}%"
            })
        
        # Display as a table
        chapter_df = pd.DataFrame(chapter_data)
        st.dataframe(chapter_df, use_container_width=True, hide_index=True)
        
        # Visual representation
        for chapter, chapter_stat in stats['chapter_stats'].items():
            chapter_correct = chapter_stat['correct']
            chapter_asked = chapter_stat['asked']
            chapter_percentage = (chapter_correct / chapter_asked * 100) if chapter_asked > 0 else 0
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**Chapter {chapter}:**")
            with col2:
                st.write(f"{chapter_correct}/{chapter_asked} correct ({chapter_percentage:.1f}%)")
                st.progress(chapter_percentage / 100)
    else:
        st.info("No chapter statistics available.")
    
    # Show missed questions summary
    if stats['missed_questions']:
        st.subheader("❌ Missed Questions Summary")
        
        # Count missed questions by chapter
        missed_by_chapter = {}
        for question in stats['missed_questions']:
            chapter = question['chapter']
            missed_by_chapter[chapter] = missed_by_chapter.get(chapter, 0) + 1
        
        # Display missed questions by chapter
        st.write("**Missed Questions by Chapter:**")
        for chapter, count in missed_by_chapter.items():
            st.write(f"- Chapter {chapter}: {count} questions")
        
        # Option to review missed questions immediately
        if st.button("🔍 Review Missed Questions Now"):
            st.session_state.show_results = False
            st.rerun()
    
    # Quiz details
    st.subheader("ℹ️ Quiz Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Class:** {stats.get('class_name', 'N/A')}")
        st.write(f"**Chapters:** {', '.join(stats.get('selected_chapters', []))}")
    
    with col2:
        if 'start_time' in stats:
            duration = datetime.now() - stats['start_time']
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            st.write(f"**Time Taken:** {minutes}m {seconds}s")
        
        # Date of quiz
        from datetime import datetime
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retry Same Quiz", use_container_width=True):
            # Reset and restart with same settings
            st.session_state.quiz_started = True
            st.session_state.quiz_completed = False
            st.session_state.show_results = False
            st.session_state.current_question = 0
            st.session_state.user_answers = [None] * len(st.session_state.current_quiz)
            st.rerun()
    
    with col2:
        if st.button("📝 New Quiz", type="primary", use_container_width=True):
            st.session_state.show_results = False
            st.rerun()
    
    with col3:
        if st.button("📊 View Full History", use_container_width=True):
            # Navigate to history page
            st.session_state.show_results = False
            # You might want to set a navigation state here
            st.info("Navigate to 'Quiz History' in the sidebar to see all your quiz attempts.")

def review_missed_questions(quiz_manager):
    st.header("📝 Review Missed Questions")
    
    if not quiz_manager.current_stats['missed_questions']:
        st.info("No missed questions to review from the last session.")
        
        # Option to go back to results if we just finished a quiz
        if st.session_state.get('show_results', False):
            if st.button("← Back to Quiz Results"):
                st.session_state.show_results = True
                st.rerun()
        return
    
    missed_questions = quiz_manager.current_stats['missed_questions']
    
    st.write(f"**Total Missed:** {len(missed_questions)} questions")
    
    for i, question in enumerate(missed_questions, 1):
        with st.expander(f"Missed Question {i} (Chapter: {question['chapter']})"):
            st.write(f"**Question:** {question['question_text']}")
            st.write(f"**Your Answer:** ❌ {question['user_answer']}")
            st.write(f"**Correct Answer:** ✅ {question['correct_answer']}")
            st.write(f"**Reasoning:** {question['reasoning']}")
    
    # Back button to results
    if st.button("← Back to Quiz Results"):
        st.session_state.show_results = True
        st.rerun()
        
def show_quiz_history(quiz_manager):
    st.header("📊 Quiz History")
    
    history_df = quiz_manager.get_history_df()
    
    if history_df.empty:
        st.info("No quiz history available yet.")
        return
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quizzes", len(history_df))
    
    with col2:
        avg_score = history_df['Correct Answers'].sum() / history_df['Total Questions'].sum() * 100
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col3:
        total_questions = history_df['Total Questions'].sum()
        st.metric("Total Questions", total_questions)
    
    with col4:
        st.metric("Best Score", history_df['Percentage'].max())
    
    # Display history table
    st.dataframe(history_df, use_container_width=True)
    
    # Progress chart
    if len(history_df) > 1:
        chart_data = history_df.copy()
        chart_data['Percentage Numeric'] = chart_data['Percentage'].str.rstrip('%').astype('float')
        st.line_chart(chart_data.set_index('Date')['Percentage Numeric'])

def export_history(quiz_manager):
    st.header("💾 Export History")
    
    if not quiz_manager.history:
        st.warning("No history available to export.")
        return
    
    history_df = quiz_manager.get_history_df()
    
    # Convert DataFrame to CSV
    csv = history_df.to_csv(index=False)
    
    st.download_button(
        label="Download History as CSV",
        data=csv,
        file_name=f"quiz_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Also show option to export missed questions
    if quiz_manager.current_stats['missed_questions']:
        missed_data = []
        for q in quiz_manager.current_stats['missed_questions']:
            missed_data.append({
                'Chapter': q['chapter'],
                'Question': q['question_text'],
                'Your Answer': q['user_answer'],
                'Correct Answer': q['correct_answer'],
                'Reasoning': q['reasoning']
            })
        
        missed_df = pd.DataFrame(missed_data)
        missed_csv = missed_df.to_csv(index=False)
        
        st.download_button(
            label="Download Missed Questions as CSV",
            data=missed_csv,
            file_name=f"missed_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
