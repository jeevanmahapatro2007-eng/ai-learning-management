from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import User, StudentProfile, InstructorProfile
from apps.courses.models import Category, Skill, Course, Lesson, LearningMaterial, Enrollment
from apps.quizzes.models import Quiz, Question, Answer
from apps.gamification.models import Badge
from apps.core.models import FAQ


class Command(BaseCommand):
    help = 'Seeds Lodestar with demo categories, skills, users, courses, lessons, quizzes and badges.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding Lodestar demo data...')

        self._seed_badges()
        self._seed_faqs()
        categories = self._seed_categories()
        skills = self._seed_skills(categories)
        admin = self._seed_admin()
        instructor = self._seed_instructor()
        student = self._seed_student()
        courses = self._seed_courses(categories, skills, instructor)
        self._seed_quizzes(courses, skills, instructor)
        self._seed_enrollment(student, courses)

        self.stdout.write(self.style.SUCCESS(
            'Done. Login as admin/admin123, instructor/instructor123, or student/student123.'
        ))

    def _seed_badges(self):
        badges = [
            (Badge.BadgeCode.FIRST_COURSE, 'First Course Completed', 'Finished your very first course.', 10),
            (Badge.BadgeCode.QUIZ_MASTER, 'Quiz Master', 'Scored 80%+ on five quizzes.', 25),
            (Badge.BadgeCode.STREAK_7, '7-Day Learning Streak', 'Learned something every day for a week.', 20),
            (Badge.BadgeCode.PYTHON_BEGINNER, 'Python Beginner', 'Completed the Python Foundations course.', 15),
            (Badge.BadgeCode.CONSISTENT_LEARNER, 'Consistent Learner', 'Logged in and studied regularly.', 15),
            (Badge.BadgeCode.FIVE_COURSES, 'Five Courses Completed', 'Completed five courses on Lodestar.', 40),
            (Badge.BadgeCode.PERFECT_SCORE, 'Perfect Score', 'Scored 100% on a quiz.', 20),
        ]
        for code, name, desc, points in badges:
            Badge.objects.get_or_create(code=code, defaults={'name': name, 'description': desc, 'points_reward': points})

    def _seed_faqs(self):
        faqs = [
            ('What makes Lodestar "personalized"?',
             'Every recommendation you see is generated from your own skill assessments, quiz results and stated interests — not a fixed syllabus.'),
            ('Do I need any experience to start?',
             'No. The onboarding skill assessment places you at the right starting point, whether that is absolute basics or an advanced topic.'),
            ('Is Lodestar free to use?',
             'This is an academic/demo build — there is no payment flow. All courses are freely enrollable.'),
            ('Can instructors publish their own courses?',
             'Yes. Instructor accounts are reviewed by an admin before their courses go live, to keep quality consistent.'),
        ]
        for i, (q, a) in enumerate(faqs):
            FAQ.objects.get_or_create(question=q, defaults={'answer': a, 'order': i})

    def _seed_categories(self):
        names = ['Python Programming', 'Web Development', 'Data Science', 'Machine Learning', 'Databases']
        cats = {}
        for n in names:
            cat, _ = Category.objects.get_or_create(name=n)
            cats[n] = cat
        return cats

    def _seed_skills(self, categories):
        mapping = {
            'Python Programming': ['Python Basics', 'Variables', 'Conditions', 'Loops', 'Functions', 'OOP in Python', 'File Handling'],
            'Web Development': ['HTML & CSS', 'JavaScript Basics', 'Django Fundamentals', 'REST APIs'],
            'Data Science': ['NumPy', 'Pandas', 'Data Visualization'],
            'Machine Learning': ['Supervised Learning', 'Model Evaluation'],
            'Databases': ['SQL Basics', 'Database Design'],
        }
        skills = {}
        for cat_name, skill_names in mapping.items():
            for s in skill_names:
                skill, _ = Skill.objects.get_or_create(name=s, defaults={'category': categories[cat_name]})
                skills[s] = skill
        return skills

    def _seed_admin(self):
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin', email='admin@lodestar.edu', password='admin123',
                first_name='Platform', last_name='Admin',
            )
            admin.role = User.Role.ADMIN
            admin.save()
            return admin
        return User.objects.get(username='admin')

    def _seed_instructor(self):
        instructor, created = User.objects.get_or_create(
            username='instructor',
            defaults=dict(
                email='instructor@lodestar.edu', first_name='Asha', last_name='Rao',
                role=User.Role.INSTRUCTOR, is_instructor_approved=True,
            )
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            InstructorProfile.objects.get_or_create(
                user=instructor,
                defaults=dict(bio='Backend engineer and Python instructor.', expertise='Python, Django, REST APIs', years_of_experience=6)
            )
        return instructor

    def _seed_student(self):
        student, created = User.objects.get_or_create(
            username='student',
            defaults=dict(email='student@lodestar.edu', first_name='Rahul', last_name='Nair', role=User.Role.STUDENT)
        )
        if created:
            student.set_password('student123')
            student.save()
            StudentProfile.objects.get_or_create(
                user=student,
                defaults=dict(
                    education='B.Tech CSE, 2nd year', interests='Python, AI, Web Development',
                    preferred_domains='Python Programming, Web Development', current_level='beginner',
                    learning_goals='Get comfortable with backend development using Django.',
                )
            )
        return student

    def _seed_courses(self, categories, skills, instructor):
        course_defs = [
            {
                'title': 'Python Foundations',
                'category': 'Python Programming',
                'difficulty': Course.Difficulty.BEGINNER,
                'duration_hours': 8,
                'short_description': 'Start from zero: variables, conditions, loops and functions.',
                'description': 'A hands-on introduction to Python covering everything you need before tackling OOP and real projects.',
                'objectives': 'Understand variables and data types\nWrite conditional logic\nUse loops confidently\nWrite reusable functions',
                'skills': ['Python Basics', 'Variables', 'Conditions', 'Loops', 'Functions'],
                'lessons': [
                    ('Introduction to Python', Lesson.LessonType.VIDEO, ['Python Basics']),
                    ('Variables & Data Types', Lesson.LessonType.TEXT, ['Variables']),
                    ('Conditional Statements', Lesson.LessonType.TEXT, ['Conditions']),
                    ('Loops in Python', Lesson.LessonType.TEXT, ['Loops']),
                    ('Writing Functions', Lesson.LessonType.PROJECT, ['Functions']),
                ],
            },
            {
                'title': 'Python Functions Deep Dive',
                'category': 'Python Programming',
                'difficulty': Course.Difficulty.INTERMEDIATE,
                'duration_hours': 5,
                'short_description': 'Master functions, arguments, scope and recursion.',
                'description': 'For learners who know Python basics but want to get fluent with functions before moving to OOP.',
                'objectives': 'Use default and keyword arguments\nUnderstand variable scope\nWrite recursive functions',
                'skills': ['Functions'],
                'lessons': [
                    ('Function Arguments Explained', Lesson.LessonType.TEXT, ['Functions']),
                    ('Scope and Closures', Lesson.LessonType.TEXT, ['Functions']),
                    ('Recursion Practice', Lesson.LessonType.PROJECT, ['Functions']),
                ],
            },
            {
                'title': 'Object-Oriented Python',
                'category': 'Python Programming',
                'difficulty': Course.Difficulty.INTERMEDIATE,
                'duration_hours': 7,
                'short_description': 'Classes, objects, inheritance and encapsulation.',
                'description': 'Move from procedural scripts to well-structured, object-oriented Python code.',
                'objectives': 'Define classes and objects\nUse inheritance effectively\nApply encapsulation principles',
                'skills': ['OOP in Python'],
                'lessons': [
                    ('Classes & Objects', Lesson.LessonType.VIDEO, ['OOP in Python']),
                    ('Inheritance', Lesson.LessonType.TEXT, ['OOP in Python']),
                    ('Mini Project: Library System', Lesson.LessonType.PROJECT, ['OOP in Python']),
                ],
            },
            {
                'title': 'Django Fundamentals',
                'category': 'Web Development',
                'difficulty': Course.Difficulty.INTERMEDIATE,
                'duration_hours': 12,
                'short_description': 'Build your first full-stack web app with Django.',
                'description': 'Covers models, views, templates, forms and the Django admin — everything to ship a working web app.',
                'objectives': 'Build models and migrations\nWrite views and templates\nHandle forms and validation',
                'skills': ['Django Fundamentals', 'HTML & CSS'],
                'lessons': [
                    ('Django Project Structure', Lesson.LessonType.VIDEO, ['Django Fundamentals']),
                    ('Models & Migrations', Lesson.LessonType.TEXT, ['Django Fundamentals']),
                    ('Templates & Views', Lesson.LessonType.TEXT, ['Django Fundamentals', 'HTML & CSS']),
                    ('Build a Mini Blog', Lesson.LessonType.PROJECT, ['Django Fundamentals']),
                ],
            },
            {
                'title': 'REST APIs with Django',
                'category': 'Web Development',
                'difficulty': Course.Difficulty.ADVANCED,
                'duration_hours': 6,
                'short_description': 'Design and build JSON APIs for your Django apps.',
                'description': 'Learn to expose your Django models as clean, well-structured JSON APIs.',
                'objectives': 'Design RESTful endpoints\nHandle authentication\nReturn structured JSON responses',
                'skills': ['REST APIs', 'Django Fundamentals'],
                'lessons': [
                    ('API Design Principles', Lesson.LessonType.TEXT, ['REST APIs']),
                    ('Building JSON Endpoints', Lesson.LessonType.PROJECT, ['REST APIs']),
                ],
            },
            {
                'title': 'SQL & Database Design Essentials',
                'category': 'Databases',
                'difficulty': Course.Difficulty.BEGINNER,
                'duration_hours': 4,
                'short_description': 'Learn to model and query relational databases.',
                'description': 'Covers tables, relationships, normalization and writing SQL queries with confidence.',
                'objectives': 'Write SELECT/JOIN queries\nDesign normalized schemas',
                'skills': ['SQL Basics', 'Database Design'],
                'lessons': [
                    ('Tables & Relationships', Lesson.LessonType.TEXT, ['Database Design']),
                    ('Writing SQL Queries', Lesson.LessonType.TEXT, ['SQL Basics']),
                ],
            },
            {
                'title': 'Data Analysis with Pandas',
                'category': 'Data Science',
                'difficulty': Course.Difficulty.INTERMEDIATE,
                'duration_hours': 6,
                'short_description': 'Clean, explore and visualize data with Pandas.',
                'description': 'A practical introduction to the Pandas library for real-world data analysis tasks.',
                'objectives': 'Load and clean datasets\nExplore data with Pandas\nVisualize key trends',
                'skills': ['Pandas', 'NumPy', 'Data Visualization'],
                'lessons': [
                    ('Getting Started with Pandas', Lesson.LessonType.VIDEO, ['Pandas']),
                    ('Cleaning Real-World Data', Lesson.LessonType.TEXT, ['Pandas']),
                    ('Visualizing Results', Lesson.LessonType.PROJECT, ['Data Visualization']),
                ],
            },
            {
                'title': 'Machine Learning Foundations',
                'category': 'Machine Learning',
                'difficulty': Course.Difficulty.ADVANCED,
                'duration_hours': 10,
                'short_description': 'Understand supervised learning and how to evaluate models.',
                'description': 'A conceptual and practical grounding in supervised machine learning.',
                'objectives': 'Understand supervised learning\nEvaluate model performance\nAvoid overfitting',
                'skills': ['Supervised Learning', 'Model Evaluation'],
                'lessons': [
                    ('What is Supervised Learning?', Lesson.LessonType.VIDEO, ['Supervised Learning']),
                    ('Evaluating Models', Lesson.LessonType.TEXT, ['Model Evaluation']),
                ],
            },
        ]

        courses = []
        for cd in course_defs:
            course, created = Course.objects.get_or_create(
                title=cd['title'],
                defaults=dict(
                    category=categories[cd['category']], instructor=instructor,
                    difficulty=cd['difficulty'], status=Course.Status.PUBLISHED,
                    duration_hours=cd['duration_hours'], short_description=cd['short_description'],
                    description=cd['description'], learning_objectives=cd['objectives'],
                )
            )
            if created:
                course.skills_covered.set([skills[s] for s in cd['skills']])
                for order, (title, ltype, lskills) in enumerate(cd['lessons'], start=1):
                    lesson = Lesson.objects.create(
                        course=course, title=title, lesson_type=ltype, order=order,
                        estimated_minutes=15, content=f'Lesson content for {title}.',
                    )
                    lesson.skills.set([skills[s] for s in lskills])
            courses.append(course)
        return courses

    def _seed_quizzes(self, courses, skills, instructor):
        # Skill-assessment quiz (section 4)
        assessment, created = Quiz.objects.get_or_create(
            title='Python Skill Assessment',
            defaults=dict(
                quiz_type=Quiz.QuizType.SKILL_ASSESSMENT,
                description='A quick check of your current Python knowledge, used to personalize your recommendations.',
                pass_mark_percent=0, created_by=instructor,
            )
        )
        if created:
            assessment.skills.set([skills['Variables'], skills['Conditions'], skills['Loops'], skills['Functions']])
            qa_data = [
                ('What does the following print? x = 5; print(x + 2)', 'Variables', [
                    ('7', True), ('5', False), ('Error', False), ('52', False),
                ]),
                ('Which keyword starts a conditional block in Python?', 'Conditions', [
                    ('if', True), ('when', False), ('check', False), ('cond', False),
                ]),
                ('What does `for i in range(3):` iterate over?', 'Loops', [
                    ('0, 1, 2', True), ('1, 2, 3', False), ('0, 1, 2, 3', False), ('3, 2, 1', False),
                ]),
                ('How do you define a function in Python?', 'Functions', [
                    ('def my_func():', True), ('function my_func():', False),
                    ('func my_func():', False), ('define my_func():', False),
                ]),
                ('What is the output of `3 == 3.0` in Python?', 'Conditions', [
                    ('True', True), ('False', False), ('Error', False), ('None', False),
                ]),
            ]
            for order, (qtext, skill_name, answers) in enumerate(qa_data, start=1):
                q = Question.objects.create(quiz=assessment, text=qtext, skill=skills[skill_name], points=1, order=order)
                for atext, correct in answers:
                    Answer.objects.create(question=q, text=atext, is_correct=correct)

        # A course-level quiz for the Python Foundations course
        foundations = next((c for c in courses if c.title == 'Python Foundations'), None)
        if foundations:
            quiz, created = Quiz.objects.get_or_create(
                title='Python Foundations Checkpoint',
                defaults=dict(
                    quiz_type=Quiz.QuizType.COURSE_QUIZ, course=foundations,
                    description='Check your understanding of the course so far.',
                    pass_mark_percent=60, created_by=instructor,
                )
            )
            if created:
                quiz.skills.set([skills['Loops'], skills['Functions']])
                data = [
                    ('What will `for i in range(2, 8, 2): print(i)` output?', 'Loops', [
                        ('2 4 6', True), ('2 4 6 8', False), ('0 2 4 6', False), ('2 3 4 5 6 7', False),
                    ]),
                    ('A function without a `return` statement returns what?', 'Functions', [
                        ('None', True), ('0', False), ('An error', False), ('An empty string', False),
                    ]),
                ]
                for order, (qtext, skill_name, answers) in enumerate(data, start=1):
                    q = Question.objects.create(quiz=quiz, text=qtext, skill=skills[skill_name], points=1, order=order)
                    for atext, correct in answers:
                        Answer.objects.create(question=q, text=atext, is_correct=correct)

    def _seed_enrollment(self, student, courses):
        foundations = next((c for c in courses if c.title == 'Python Foundations'), None)
        if foundations:
            Enrollment.objects.get_or_create(student=student, course=foundations)
