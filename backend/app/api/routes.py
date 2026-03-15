import json
from pathlib import Path

from flask import Blueprint, Response, jsonify, request
from werkzeug.utils import secure_filename

from app.models.db import db
from app.models.entities import FileRecord, Project, QaItem, Report, SceneSuggestion, Slide
from app.parsers.file_parser import parse_file
from app.services.core_services import build_report, generate_qa, generate_scene_suggestions, run_evaluation

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


@api_bp.post("/projects/bootstrap_demo")
def bootstrap_demo():
    project = Project(name="演析 Pro 示例项目", scene_type="competition", target_minutes=8)
    db.session.add(project)
    db.session.commit()

    demo_path = UPLOAD_DIR / f"p{project.id}_demo_script.txt"
    demo_path.write_text(
        "项目背景\n我们解决答辩训练低效问题。\n\n"
        "方案设计\n提出解析-重构-问答-评估闭环。\n\n"
        "实验结果\n相比传统练习，准备效率提升40%。\n\n"
        "总结与展望\n下一步接入语音评分与多轮追问。\n",
        encoding="utf-8",
    )

    record = FileRecord(
        project_id=project.id,
        file_name="demo_script.txt",
        file_type="txt",
        file_path=str(demo_path),
        parse_status="pending",
    )
    db.session.add(record)
    db.session.commit()

    return ok({"project_id": project.id, "file_id": record.id})


@api_bp.get("/projects")
def list_projects():
    rows = Project.query.order_by(Project.id.desc()).all()
    return ok([
        {"id": p.id, "name": p.name, "scene_type": p.scene_type, "target_minutes": p.target_minutes}
        for p in rows
    ])


@api_bp.post("/files/upload")
def upload_file():
    project_id = int(request.form.get("project_id", 0))
    if "file" not in request.files:
        return jsonify({"code": 1, "message": "缺少文件", "data": {}}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"txt", "pdf", "pptx"}:
        return jsonify({"code": 1, "message": "仅支持 txt/pdf/pptx", "data": {}}), 400

    save_name = f"p{project_id}_{filename}"
    save_path = UPLOAD_DIR / save_name
    f.save(save_path)

    record = FileRecord(project_id=project_id, file_name=filename, file_type=ext, file_path=str(save_path), parse_status="pending")
    db.session.add(record)
    db.session.commit()

    return ok({"file_id": record.id, "file_name": filename})


@api_bp.post("/analysis/parse/<int:file_id>")
def parse(file_id: int):
    rec = FileRecord.query.get_or_404(file_id)
    data = parse_file(rec.file_path, rec.file_type)

    Slide.query.filter_by(file_id=file_id).delete()
    for row in data:
        db.session.add(
            Slide(
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
        )

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
    return ok(
        [
            {
                "page_no": r["page_no"],
                "title_guess": r["title_guess"],
                "text_count": r["text_count"],
                "is_key_page": r["is_key_page"],
                "risk_tags": json.loads(r["risk_tags"] or "[]"),
                "logic_score": r["logic_score"],
            }
            for r in rows
        ]
    )


@api_bp.post("/scene/rewrite/<int:project_id>")
def scene_rewrite(project_id: int):
    payload = request.get_json(silent=True) or {}
    project = Project.query.get_or_404(project_id)
    scene_type = payload.get("scene_type", project.scene_type)
    project.scene_type = scene_type

    count = generate_scene_suggestions(project_id, scene_type)
    db.session.commit()
    return ok({"count": count, "scene_type": scene_type})


@api_bp.get("/scene/project/<int:project_id>")
def scene_list(project_id: int):
    rows = SceneSuggestion.query.filter_by(project_id=project_id).order_by(SceneSuggestion.priority.asc()).all()
    return ok(
        [
            {
                "scene_type": r.scene_type,
                "suggestion_type": r.suggestion_type,
                "content": r.content,
                "priority": r.priority,
            }
            for r in rows
        ]
    )


@api_bp.post("/qa/generate/<int:project_id>")
def qa_generate(project_id: int):
    count = generate_qa(project_id)
    return ok({"count": count})


@api_bp.get("/qa/project/<int:project_id>")
def qa_list(project_id: int):
    rows = QaItem.query.filter_by(project_id=project_id).order_by(QaItem.page_no.asc()).all()
    return ok([{"page_no": r.page_no, "qa_type": r.qa_type, "question": r.question, "reference_answer": r.reference_answer} for r in rows])


@api_bp.post("/evaluation/run/<int:project_id>")
def evaluate(project_id: int):
    payload = request.get_json(force=True)
    run = run_evaluation(project_id, payload.get("script_text", ""), int(payload.get("target_minutes", 10)))
    return ok(
        {
            "evaluation_id": run.id,
            "estimated_wpm": run.estimated_wpm,
            "coverage_score": run.coverage_score,
            "timing_score": run.timing_score,
            "expression_score": run.expression_score,
        }
    )


@api_bp.post("/reports/generate/<int:evaluation_id>")
def generate_report(evaluation_id: int):
    report = build_report(evaluation_id)
    return ok({"report_id": report.id, "total_score": report.total_score, "report_markdown": report.report_markdown})


@api_bp.get("/reports/<int:report_id>")
def get_report(report_id: int):
    r = Report.query.get_or_404(report_id)
    return ok(
        {
            "report_id": r.id,
            "total_score": r.total_score,
            "structure_score": r.structure_score,
            "qa_score": r.qa_score,
            "risk_summary": r.risk_summary,
            "report_markdown": r.report_markdown,
        }
    )


@api_bp.get("/reports/download/<int:report_id>")
def download_report(report_id: int):
    report = Report.query.get_or_404(report_id)
    return Response(
        report.report_markdown,
        mimetype="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=yanxi_report_{report_id}.md"},
    )
