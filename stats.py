"""刷题数据统计：完成题量、各专题完成情况、通过率等。"""

from extensions import db
from models import MistakeNote, Problem, Submission


def _scalar_count(stmt) -> int:
    return int(db.session.scalar(stmt) or 0)


def compute_stats(user_id: int) -> dict:
    problems = db.session.scalars(db.select(Problem).order_by(Problem.id)).all()
    total_problems = len(problems)

    ac_ids = set(
        db.session.scalars(
            db.select(Submission.problem_id)
            .where(Submission.user_id == user_id, Submission.status == "AC")
            .distinct()
        ).all()
    )
    tried_ids = set(
        db.session.scalars(
            db.select(Submission.problem_id).where(Submission.user_id == user_id).distinct()
        ).all()
    )

    total_submits = _scalar_count(
        db.select(db.func.count(Submission.id)).where(Submission.user_id == user_id)
    )
    ac_submits = _scalar_count(
        db.select(db.func.count(Submission.id)).where(
            Submission.user_id == user_id, Submission.status == "AC"
        )
    )
    mistake_count = _scalar_count(
        db.select(db.func.count(MistakeNote.id)).where(MistakeNote.user_id == user_id)
    )

    by_difficulty = {}
    for level in ("入门", "基础"):
        items = [p for p in problems if p.difficulty == level]
        solved = [p for p in items if p.id in ac_ids]
        by_difficulty[level] = {
            "total": len(items),
            "solved": len(solved),
            "percent": round(len(solved) / len(items) * 100) if items else 0,
        }

    tag_names = []
    for problem in problems:
        for tag in problem.tag_list:
            if tag not in tag_names:
                tag_names.append(tag)

    by_tag = []
    for tag in tag_names:
        items = [p for p in problems if tag in p.tag_list]
        solved = [p for p in items if p.id in ac_ids]
        by_tag.append(
            {
                "tag": tag,
                "total": len(items),
                "solved": len(solved),
                "percent": round(len(solved) / len(items) * 100) if items else 0,
            }
        )
    by_tag.sort(key=lambda x: (-x["percent"], x["tag"]))

    return {
        "total_problems": total_problems,
        "solved": len(ac_ids),
        "attempted": len(tried_ids),
        "unsolved_attempted": len(tried_ids - ac_ids),
        "total_submits": total_submits,
        "ac_submits": ac_submits,
        "pass_rate": round(ac_submits / total_submits * 100, 1) if total_submits else 0.0,
        "completion": round(len(ac_ids) / total_problems * 100) if total_problems else 0,
        "mistakes": mistake_count,
        "by_difficulty": by_difficulty,
        "by_tag": by_tag,
        "solved_ids": ac_ids,
        "tried_ids": tried_ids,
    }
