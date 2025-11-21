# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 15:46:54 2025

@author: hubba
"""

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
        selected_questions = all_questions[:num_questions]
        
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
    st.set_page_config(
        page_title="Quiz Master",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()
    
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    
    quiz_manager = st.session_state.quiz_manager
    
    # Sidebar
    st.sidebar.title("📚 Quiz Master")
    st.sidebar.markdown("---")
    
    # Main navigation
    menu_options = [
        "Load Quiz Set",
        "Take Quiz", 
        "View All Questions",
        "Review Missed Questions",
        "Quiz History",
        "Export History"
    ]
    selected_menu = st.sidebar.selectbox("Navigation", menu_options)
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Upload a CSV file with columns: Chapter, Question Text, Reasoning, "
        "Correct_Answer, Alternative_1, Alternative_2, Alternative_3"
    )
    
    # Main content area
    st.title("🎯 Quiz Master")
    
    if selected_menu == "Load Quiz Set":
        load_quiz_set(quiz_manager)
    
    elif selected_menu == "Take Quiz":
        take_quiz(quiz_manager)
    
    elif selected_menu == "View All Questions":
        view_all_questions(quiz_manager)
    
    elif selected_menu == "Review Missed Questions":
        review_missed_questions(quiz_manager)
    
    elif selected_menu == "Quiz History":
        show_quiz_history(quiz_manager)
    
    elif selected_menu == "Export History":
        export_history(quiz_manager)

def load_quiz_set(quiz_manager):
    st.header("📥 Load Quiz Set")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            # Read and display the file
            try:
                df = pd.read_csv(uploaded_file)
                st.success("CSV file loaded successfully!")
                st.dataframe(df.head(), use_container_width=True)
                
                class_name = st.text_input("Class Name", value=uploaded_file.name.replace('.csv', ''))
                
                if st.button("Load Questions"):
                    success, result = quiz_manager.load_csv(None, uploaded_file)
                    if success:
                        quiz_manager.quizzes[class_name] = result
                        st.success(f"✅ Loaded {sum(len(q) for q in result.values())} questions from {len(result)} chapters for class '{class_name}'")
                    else:
                        st.error(f"❌ {result}")
                        
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
    
    with col2:
        st.subheader("Loaded Classes")
        if quiz_manager.quizzes:
            for class_name, chapters in quiz_manager.quizzes.items():
                total_questions = sum(len(questions) for questions in chapters.values())
                st.write(f"**{class_name}**: {total_questions} questions across {len(chapters)} chapters")
        else:
            st.info("No classes loaded yet. Upload a CSV file to get started.")

def take_quiz(quiz_manager):
    st.header("🎯 Take Quiz")
    
    if not quiz_manager.quizzes:
        st.warning("Please load a quiz set first from the 'Load Quiz Set' page.")
        return
    
    # Quiz setup
    col1, col2 = st.columns(2)
    
    with col1:
        class_name = st.selectbox("Select Class", list(quiz_manager.quizzes.keys()))
        chapter_questions = quiz_manager.quizzes[class_name]
        available_chapters = list(chapter_questions.keys())
        
        selected_chapters = st.multiselect(
            "Select Chapters", 
            available_chapters,
            default=available_chapters
        )
    
    with col2:
        total_available = sum(len(chapter_questions[ch]) for ch in selected_chapters) if selected_chapters else 0
        max_questions = st.number_input(
            "Number of Questions", 
            min_value=1, 
            max_value=total_available, 
            value=min(10, total_available) if total_available > 0 else 1
        )
        
        if total_available == 0:
            st.warning("No questions available for selected chapters.")
            return
    
    if st.button("Start Quiz") and selected_chapters:
        success, questions = quiz_manager.start_quiz(class_name, selected_chapters, max_questions, chapter_questions)
        if success:
            st.session_state.current_quiz = questions
            st.session_state.quiz_started = True
            st.session_state.quiz_completed = False
            st.session_state.current_question = 0
            st.session_state.user_answers = [None] * len(questions)
            st.rerun()
        else:
            st.error(questions)
    
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
                quiz_manager.save_quiz_session()
                st.rerun()

    # Show progress
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.write(f"Progress: {current_idx + 1}/{len(questions)} questions")

def view_all_questions(quiz_manager):
    st.header("📋 All Questions")
    
    if not quiz_manager.quizzes:
        st.warning("Please load a quiz set first from the 'Load Quiz Set' page.")
        return
    
    class_name = st.selectbox("Select Class", list(quiz_manager.quizzes.keys()), key="view_class")
    chapter_questions = quiz_manager.quizzes[class_name]
    
    # Create expanders for each chapter
    for chapter, questions in chapter_questions.items():
        with st.expander(f"Chapter: {chapter} ({len(questions)} questions)"):
            for i, question in enumerate(questions, 1):
                st.write(f"**Q{i}:** {question['question_text']}")
                st.write(f"**Correct Answer:** {question['correct_answer']}")
                st.write(f"**Alternatives:** {', '.join(question['alternatives'])}")
                st.write(f"**Reasoning:** {question['reasoning']}")
                st.markdown("---")

def review_missed_questions(quiz_manager):
    st.header("📝 Review Missed Questions")
    
    if not quiz_manager.current_stats['missed_questions']:
        st.info("No missed questions to review from the last session.")
        return
    
    missed_questions = quiz_manager.current_stats['missed_questions']
    
    st.write(f"**Total Missed:** {len(missed_questions)} questions")
    
    for i, question in enumerate(missed_questions, 1):
        with st.expander(f"Missed Question {i} (Chapter: {question['chapter']})"):
            st.write(f"**Question:** {question['question_text']}")
            st.write(f"**Your Answer:** ❌ {question['user_answer']}")
            st.write(f"**Correct Answer:** ✅ {question['correct_answer']}")
            st.write(f"**Reasoning:** {question['reasoning']}")

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