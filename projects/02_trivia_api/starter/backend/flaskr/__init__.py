import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    '''
    Create an endpoint to handle GET requests for all available categories
    '''
    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        selection = Category.query.order_by(Category.id).all()

        if len(selection) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": {cat.id:cat.type for cat in selection},
            }
        )

    '''
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''
    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        categories = {cat.id:cat.type for cat in categories}
        if len(selection) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(selection),
                "categories": categories,
                "currentCategory": None,
            }
        )

    '''
    Create an endpoint to DELETE question using a question ID. 

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            categories = Category.query.order_by(Category.id).all()
            categories = {cat.id:cat.type for cat in categories}

            if len(selection) == 0:
                abort(404)

            return jsonify(
                {
                    "success": True,
                    'deleted': question_id,
                    "questions": current_questions,
                    "total_questions": len(selection),
                    "categories": categories,
                    "current_category": None,
                }
            )
        except:
            abort(422)

    '''
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.    
    
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 

    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question')
        new_answer = body.get('answer')
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')
        searchTerm = body.get('searchTerm')

        try:
            if searchTerm:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f"%{searchTerm}%")
                )
                current_questions = paginate_questions(request, selection)
                categories = Category.query.order_by(Category.id).all()
                categories = {cat.id:cat.type for cat in categories}

                if len(current_questions) == 0:
                    abort(404)

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all()),
                        "categories": categories,
                        "current_category": None,
                    }
                )

            else:
                question = Question(
                    question=new_question, 
                    answer=new_answer, 
                    category=new_category,
                    difficulty=new_difficulty,
                    )
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)
                categories = Category.query.order_by(Category.id).all()
                categories = {cat.id:cat.type for cat in categories}

                if len(selection) == 0:
                    abort(404)

                return jsonify(
                    {
                        "success": True,
                        'created': question.id,
                        "questions": current_questions,
                        "total_questions": len(selection),
                        "categories": categories,
                        "current_category": None,
                    }
                )

        except Exception as e:
            print(e)
            abort(422)

    '''
    Create a GET endpoint to get questions based on category. 

    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category_id(category_id):
        selection = Question.query.filter(Question.category==category_id).order_by(Question.id).all()

        if len(selection) == 0:
            abort(404)
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        categories = {cat.id:cat.type for cat in categories}

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(selection),
                "categories": categories,
                "currentCategory": category_id,
            }
        )

    '''
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''
    @app.route('/quizzes', methods=['POST'])
    def play_quizzes():
        data = request.get_json()
        quiz_category = data['quiz_category']
        previous_questions = data['previous_questions']

        if quiz_category:
            next_question = Question.query.filter(Question.category==quiz_category['id'], 
                Question.id.notin_(previous_questions)).order_by(func.random()).first()
        else:
            next_question = Question.query.filter(Question.id.notin_(previous_questions)).order_by(func.random()).first()
        
        if next_question:
            previous_questions.append(next_question.id)
            next_question = next_question.format()
        return jsonify(
            {
                "success": True,
                "question": next_question,
                "previous_questions": previous_questions,
            }
        )


    '''
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "success": False, 
                "error": 404, 
                "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                "success": False, 
                "error": 422, 
                "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False, 
            "error": 400, 
            "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({
                "success": False, 
                "error": 405, 
                "message": "method not allowed"}),
            405,
        )
    
    return app

    