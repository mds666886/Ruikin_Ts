import json

from app.models.db import db
from app.models.entities import QaItem, Slide, EvaluationRun, Report


QA_TYPES = ["basic", "followup", "challenge", "compare", "apply"]


def generate_qa(project_id: int):
    Slide.query.join(
        db.text("files ON files.id = slides.file_id")
    ).filter(db.text("files.project_id = :pid")).params(pid=project_id).all()

    existing = QaItem.query.filter_by(project_id=project_id).all()
    for item in existing:
        db.session.delete(item)

    slides = db.session.execute(
        db.text(
            "SELECT s.page_no, s.title_guess, s.summary FROM slides s "
            "JOIN files f ON s.file_id=f.id WHERE f.project_id=:pid ORDER BY s.page_no"
        ),
        {"pid": project_id},
    ).fetchall()

    created = []
    for s in slides:
        for qa_type in QA_TYPES:
            q = f"[{qa_type}] 第{s.page_no}页《{s.title_guess}》可能会被问到什么？"
            a = f"建议围绕该页核心内容回答：{(s.summary or '请补充讲稿')[:80]}"
            item = QaItem(project_id=project_id, page_no=s.page_no, qa_type=qa_type, question=q, reference_answer=a, difficulty=3)
            db.session.add(item)
            created.append(item)

    db.session.commit()
    return len(created)


def run_evaluation(project_id: int, script_text: str, target_minutes: int):
    char_count = len(script_text.strip())
    estimated_wpm = char_count / max(target_minutes, 1)
    timing_score = max(0, 100 - abs(estimated_wpm - 120) * 0.5)

    slide_count = db.session.execute(
        db.text("SELECT COUNT(*) FROM slides s JOIN files f ON s.file_id=f.id WHERE f.project_id=:pid"),
        {"pid": project_id},
    ).scalar_one()

    coverage_score = min(100.0, (char_count / max(200, slide_count * 80)) * 100)
    expression_score = round((timing_score * 0.5 + coverage_score * 0.5), 2)

    run = EvaluationRun(
        project_id=project_id,
        script_text=script_text,
        estimated_wpm=estimated_wpm,
        coverage_score=coverage_score,
        timing_score=timing_score,
        expression_score=expression_score,
    )
    db.session.add(run)
    db.session.commit()
    return run


def build_report(evaluation_id: int):
    run = EvaluationRun.query.get_or_404(evaluation_id)
    qa_count = QaItem.query.filter_by(project_id=run.project_id).count()

    risk_rows = db.session.execute(
        db.text(
            "SELECT s.page_no, s.risk_tags FROM slides s JOIN files f ON s.file_id=f.id WHERE f.project_id=:pid"
        ),
        {"pid": run.project_id},
    ).fetchall()

    risk_pages = []
    for row in risk_rows:
        tags = json.loads(row.risk_tags or "[]")
        if tags:
            risk_pages.append(f"第{row.page_no}页: {'/'.join(tags)}")

    structure_score = max(40, 100 - len(risk_pages) * 8)
    qa_score = min(100, qa_count * 2)
    total_score = round(structure_score * 0.35 + run.expression_score * 0.35 + qa_score * 0.3, 2)

    top_actions = [
        "先修改文字过密页面，每页控制在 6-8 行",
        "补充过渡句，减少逻辑断点",
        "针对质疑题准备 3 条数据证据",
    ]
    markdown = (
        f"# 演析 Pro 复盘报告\n\n"
        f"- 总分: {total_score}\n"
        f"- 结构分: {structure_score}\n"
        f"- 表达分: {run.expression_score}\n"
        f"- 问答准备分: {qa_score}\n\n"
        f"## 风险页\n" + ("\n".join([f"- {x}" for x in risk_pages]) if risk_pages else "- 暂无明显风险") +
        "\n\n## 优先改进\n" + "\n".join([f"- {x}" for x in top_actions])
    )

    report = Report(
        evaluation_id=run.id,
        total_score=total_score,
        structure_score=structure_score,
        qa_score=qa_score,
        risk_summary="; ".join(risk_pages[:10]),
        top_actions=json.dumps(top_actions, ensure_ascii=False),
        report_markdown=markdown,
    )
    db.session.add(report)
    db.session.commit()
    return report
