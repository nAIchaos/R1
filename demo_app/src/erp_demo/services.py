from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .domain import (
    LabelPrintLine,
    LabelPrintTask,
    MatchType,
    Member,
    PriceRule,
    PriceType,
    Product,
    ProductPackaging,
    PromotionCampaign,
    PromotionItem,
    RuleScope,
)
from .repositories import InMemoryDB


class PricingService:
    """不折上折：会员组规则价与活动价取最小值，不叠加。"""

    def __init__(self, db: InMemoryDB):
        self.db = db

    def _active_rules(self, now: datetime) -> list[PriceRule]:
        return [r for r in self.db.price_rules if r.valid_from <= now <= r.valid_to]

    def _match_rule(self, rule: PriceRule, member: Member, product: Product) -> bool:
        if rule.rule_scope == RuleScope.MEMBER and rule.member_id != member.id:
            return False
        if rule.rule_scope == RuleScope.MEMBER_GROUP and rule.member_tier != member.tier:
            return False
        if rule.match_type == MatchType.EXACT_PRODUCT:
            return rule.match_value == product.id
        if rule.match_type == MatchType.CATEGORY:
            return rule.match_value == product.category_lv1
        return False

    def _rule_to_price(self, rule: PriceRule, list_price: float) -> float:
        if rule.price_type == PriceType.FIXED_PRICE:
            return rule.value
        return round(list_price * rule.value, 2)

    def final_price(self, member_id: str, product_id: str, pack_level: str = "inner") -> float:
        now = datetime.now()
        member = self.db.members[member_id]
        product = self.db.products[product_id]
        pack = next(p for p in self.db.packaging if p.product_id == product_id and p.pack_level == pack_level)

        list_price = pack.list_price
        promo_price = pack.promo_price if pack.promo_price else list_price

        member_product_candidates: list[float] = []
        member_group_candidates: list[float] = []

        for rule in self._active_rules(now):
            if not self._match_rule(rule, member, product):
                continue
            candidate = self._rule_to_price(rule, list_price)
            if rule.rule_scope == RuleScope.MEMBER:
                member_product_candidates.append(candidate)
            else:
                member_group_candidates.append(candidate)

        if member_product_candidates:
            return min(member_product_candidates)
        if member_group_candidates:
            return min(min(member_group_candidates), promo_price)
        return min(list_price, promo_price)


@dataclass
class ReplenishmentInput:
    avg_daily_sales_30d: float
    max_daily_sales_30d: float
    cycle_days: int
    on_hand: int
    reserved: int
    in_transit: int
    safety_days: int = 7
    last_order_qty: int = 0


class ReplenishmentService:
    def suggest_order(self, data: ReplenishmentInput) -> dict[str, float]:
        forecast_demand = max(data.avg_daily_sales_30d * data.cycle_days, data.max_daily_sales_30d * data.cycle_days)
        available = data.on_hand - data.reserved + data.in_transit
        safety_stock = data.avg_daily_sales_30d * data.safety_days
        min_order_qty = max(0, forecast_demand - available + safety_stock)
        suggest_order_qty = max(min_order_qty, data.last_order_qty)
        return {
            "forecast_demand": round(forecast_demand, 2),
            "available": round(available, 2),
            "safety_stock": round(safety_stock, 2),
            "min_order_qty": round(min_order_qty, 2),
            "suggest_order_qty": round(suggest_order_qty, 2),
        }


class PromotionService:
    def __init__(self, db: InMemoryDB):
        self.db = db

    def create_campaign(self, campaign: PromotionCampaign, items: list[PromotionItem]) -> None:
        self.db.promotions.append(campaign)
        self.db.promotion_items.extend(items)

    def generate_promo_label_task(self, campaign_id: str) -> LabelPrintTask:
        task = LabelPrintTask(id=f"LBL-{campaign_id}", task_type="promo")
        lines = [it for it in self.db.promotion_items if it.campaign_id == campaign_id]
        for it in lines:
            pack = next(p for p in self.db.packaging if p.product_id == it.product_id and p.pack_level == "inner")
            promo_price = it.promo_price if it.promo_price is not None else round(pack.list_price * (it.discount_rate or 1), 2)
            task.lines.append(LabelPrintLine(product_id=it.product_id, pack_level="inner", price_to_print=promo_price, copies=1))
        self.db.label_tasks.append(task)
        return task


class LabelService:
    def __init__(self, db: InMemoryDB):
        self.db = db

    def queue_new_product_label(self, product_id: str) -> LabelPrintTask:
        task = LabelPrintTask(id=f"LBL-NORMAL-{product_id}", task_type="normal")
        for p in [x for x in self.db.packaging if x.product_id == product_id]:
            task.lines.append(LabelPrintLine(product_id=product_id, pack_level=p.pack_level, price_to_print=p.list_price))
        self.db.label_tasks.append(task)
        return task

    def queue_reprint_by_barcode_or_sku(self, query: str) -> LabelPrintTask:
        task = LabelPrintTask(id=f"LBL-REPRINT-{query}", task_type="reprint")
        packs = [p for p in self.db.packaging if p.barcode == query]
        if not packs:
            skus = [s for s in self.db.supplier_skus if s.supplier_sku == query and s.enabled]
            for sku in skus:
                packs.extend([p for p in self.db.packaging if p.product_id == sku.product_id])
        for p in packs:
            task.lines.append(LabelPrintLine(product_id=p.product_id, pack_level=p.pack_level, price_to_print=p.list_price))
        self.db.label_tasks.append(task)
        return task


class ReceivingService:
    def __init__(self, db: InMemoryDB):
        self.db = db

    def gross_margin(self, sale_price: float, purchase_price: float) -> float:
        if sale_price <= 0:
            return 0.0
        return round((sale_price - purchase_price) / sale_price, 4)

    def margin_flag(self, sale_price: float, purchase_price: float, min_margin=0.05, max_margin=0.6) -> str:
        margin = self.gross_margin(sale_price, purchase_price)
        if margin < min_margin or margin > max_margin:
            return "highlight"
        return "normal"


class ReportingService:
    def __init__(self, db: InMemoryDB):
        self.db = db

    def near_expiry_report(self, threshold_days: int = 30) -> list[dict]:
        today = date.today()
        out = []
        for s in self.db.stock_balances:
            if not s.latest_expiry_date:
                continue
            left_days = (s.latest_expiry_date - today).days
            if left_days <= threshold_days:
                product = self.db.products[s.product_id]
                out.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name_zh,
                        "left_days": left_days,
                        "qty_on_hand": s.qty_on_hand,
                    }
                )
        return sorted(out, key=lambda x: (x["left_days"], -x["qty_on_hand"]))
