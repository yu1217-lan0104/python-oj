"""Python 语法 / 算法知识点卡片：分类筛选 + 关键词搜索 + 折叠展开。"""

from flask import Blueprint, render_template, request
from sqlalchemy import select

from extensions import db
from models import Card

bp = Blueprint("cards", __name__, url_prefix="/cards")


@bp.route("/")
def index():
    cards = db.session.scalars(select(Card).order_by(Card.sort_order, Card.id)).all()
    categories = []
    for card in cards:
        if card.category not in categories:
            categories.append(card.category)

    category = (request.args.get("category") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()

    filtered = []
    for card in cards:
        if category and card.category != category:
            continue
        if keyword:
            text = (card.title + card.summary + card.content + card.tags).lower()
            if keyword.lower() not in text:
                continue
        filtered.append(card)

    grouped = {}
    for card in filtered:
        grouped.setdefault(card.category, []).append(card)

    return render_template(
        "cards/list.html",
        grouped=grouped,
        total=len(cards),
        shown=len(filtered),
        categories=categories,
        category=category,
        keyword=keyword,
    )
