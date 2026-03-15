import json
import os
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.models.db import db
from app.models.entities import Project, FileRecord, Slide, QaItem, EvaluationRun, Report
from app.parsers.file_parser import parse_file
from app.services.core_services import generate_qa, run_evaluation, build_report

api_bp = Blueprint("api", __name__)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def ok(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data or {}})


@api_bp.get("/health")
def health():
    return ok({"status": "up"})


@api_bp.post("/projects")
def create_project():
    payload = request.get_json(force=True)
    project = Project(
        name=payload.get("name", "未命名项目"),
        scene_type=payload.get("scene_type", "competition"),
        target_minutes=int(payload.get("target_minutes", 10)),
    )
    db.session.add(project)
    db.session.commit()
    return ok({"id": project.id})


@api_bp.get("/projects")
def list_projects():
    rows = Project.query.order_by(Project.id.desc()).all()
    return ok([
        {
            "id": p.id,
            "name": p.name,
            "scene_type": p.scene_type,
            "target_minutes": p.target_minutes,
        }
        for p in rows
    ])


@api_bp.post("/files/upload")
def upload_file():
    project_id = int(request.form.get("project_id", 0))
    if "file" not in request.files:
        return jsonify({"code": 1, "message": "缺少文件", "data": {}}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in {"txt", "pdf", "pptx"}:
        return jsonify({"code": 1, "message": "仅支持 txt/pdf/pptx", "data": {}}), 400

    save_name = f"p{project_id}_{filename}"
    save_path = UPLOAD_DIR / save_name
    f.save(save_path)

    record = FileRecord(
        project_id=project_id,
        file_name=filename,
        file_type=ext,
        file_path=str(save_path),
        parse_status="pending",
    )
    db.session.add(record)
    db.session.commit()

    return ok({"file_id": record.id, "file_name": filename})


@api_bp.post("/analysis/parse/<int:file_id>")
def parse(file_id: int):
    rec = FileRecord.query.get_or_404(file_id)
    data = parse_file(rec.file_path, rec.file_type)

    Slide.query.filter_by(file_id=file_id).delete()
    for row in data:
        slide = Slide(
            file_id=file_id,
            page_no=row["page_no"],
            title_guess=row["title_guess"],
            text_count=row["text_count"],
            image_ratio=row["image_ratio"],
            is_key_page=row["is_key_page"],
            risk_tags=json.dumps(row["risk_tags"], ensure_ascii=False),
            logic_score=row["logic_score"],
            summary=row["summary"],
        )
        db.session.add(slide)

    rec.parse_status = "done"
    db.session.commit()
    return ok({"slide_count": len(data)})


@api_bp.get("/analysis/project/<int:project_id>")
def analysis(project_id: int):
    rows = db.session.execute(
        db.text(
            "SELECT s.page_no, s.title_guess, s.text_count, s.is_key_page, s.risk_tags, s.logic_score "
            "FROM slides s JOIN files f ON s.file_id=f.id WHERE f.project_id=:pid ORDER BY s.page_no"
        ),
        {"pid": project_id},
    ).mappings()
    return ok([
        {
            "page_no": r["page_no"],
            "title_guess": r["title_guess"],
            "text_count": r["text_count"],
            "is_key_page": r["is_key_page"],
            "risk_tags": json.loads(r["risk_tags"] or "[]"),
            "logic_score": r["logic_score"],
        }
        for r in rows
    ])


@api_bp.post("/qa/generate/<int:project_id>")
def qa_generate(project_id: int):
    count = generate_qa(project_id)
    return ok({"count": count})


@api_bp.get("/qa/project/<int:project_id>")
def qa_list(project_id: int):
    rows = QaItem.query.filter_by(project_id=project_id).order_by(QaItem.page_no.asc()).all()
    return ok([
        {
            "page_no": r.page_no,
            "qa_type": r.qa_type,
            "question": r.question,
            "reference_answer": r.reference_answer,
        }
        for r in rows
    ])


@api_bp.post("/evaluation/run/<int:project_id>")
def evaluate(project_id: int):
    payload = request.get_json(force=True)
    run = run_evaluation(project_id, payload.get("script_text", ""), int(payload.get("target_minutes", 10)))
    return ok({
        "evaluation_id": run.id,
        "estimated_wpm": run.estimated_wpm,
        "coverage_score": run.coverage_score,
        "timing_score": run.timing_score,
        "expression_score": run.expression_score,
    })


@api_bp.post("/reports/generate/<int:evaluation_id>")
def generate_report(evaluation_id: int):
    report = build_report(evaluation_id)
    return ok({
        "report_id": report.id,
        "total_score": report.total_score,
        "report_markdown": report.report_markdown,
    })


@api_bp.get("/reports/<int:report_id>")
def get_report(report_id: int):
    r = Report.query.get_or_404(report_id)
    return ok({
        "report_id": r.id,
        "total_score": r.total_score,
        "structure_score": r.structure_score,
        "qa_score": r.qa_score,
        "risk_summary": r.risk_summary,
        "report_markdown": r.report_markdown,
    })
