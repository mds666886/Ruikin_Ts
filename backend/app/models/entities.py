from datetime import datetime

from .db import db


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    scene_type = db.Column(db.String(32), nullable=False, default="competition")
    target_minutes = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FileRecord(db.Model):
    __tablename__ = "files"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(16), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    parse_status = db.Column(db.String(16), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Slide(db.Model):
    __tablename__ = "slides"
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    page_no = db.Column(db.Integer, nullable=False)
    title_guess = db.Column(db.String(255), nullable=False, default="未命名")
    text_count = db.Column(db.Integer, nullable=False, default=0)
    image_ratio = db.Column(db.Float, nullable=False, default=0.0)
    is_key_page = db.Column(db.Integer, nullable=False, default=0)
    risk_tags = db.Column(db.Text, nullable=False, default="[]")
    logic_score = db.Column(db.Float, nullable=False, default=0.0)
    summary = db.Column(db.Text, nullable=False, default="")


class SceneSuggestion(db.Model):
    __tablename__ = "scene_suggestions"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    scene_type = db.Column(db.String(32), nullable=False)
    suggestion_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=2)


class QaItem(db.Model):
    __tablename__ = "qa_items"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    page_no = db.Column(db.Integer, nullable=False)
    qa_type = db.Column(db.String(16), nullable=False)
    question = db.Column(db.Text, nullable=False)
    reference_answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False, default=3)


class EvaluationRun(db.Model):
    __tablename__ = "evaluation_runs"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    script_text = db.Column(db.Text, nullable=False)
    estimated_wpm = db.Column(db.Float, nullable=False, default=0)
    coverage_score = db.Column(db.Float, nullable=False, default=0)
    timing_score = db.Column(db.Float, nullable=False, default=0)
    expression_score = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluation_runs.id"), nullable=False)
    total_score = db.Column(db.Float, nullable=False, default=0)
    structure_score = db.Column(db.Float, nullable=False, default=0)
    qa_score = db.Column(db.Float, nullable=False, default=0)
    risk_summary = db.Column(db.Text, nullable=False, default="")
    top_actions = db.Column(db.Text, nullable=False, default="[]")
    report_markdown = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
