from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .domain import (
    LabelPrintTask,
    Member,
    PriceRule,
    Product,
    ProductPackaging,
    PromotionCampaign,
    PromotionItem,
    StockBalance,
    StockMovement,
    Supplier,
    SupplierSKU,
)


@dataclass
class InMemoryDB:
    products: dict[str, Product] = field(default_factory=dict)
    packaging: list[ProductPackaging] = field(default_factory=list)
    suppliers: dict[str, Supplier] = field(default_factory=dict)
    supplier_skus: list[SupplierSKU] = field(default_factory=list)
    members: dict[str, Member] = field(default_factory=dict)
    price_rules: list[PriceRule] = field(default_factory=list)
    stock_balances: list[StockBalance] = field(default_factory=list)
    stock_movements: list[StockMovement] = field(default_factory=list)
    promotions: list[PromotionCampaign] = field(default_factory=list)
    promotion_items: list[PromotionItem] = field(default_factory=list)
    label_tasks: list[LabelPrintTask] = field(default_factory=list)

    def add_stock_movement(self, warehouse_id: str, product_id: str, movement_type: str, quantity: int) -> None:
        self.stock_movements.append(
            StockMovement(
                warehouse_id=warehouse_id,
                product_id=product_id,
                movement_date=datetime.now(),
                movement_type=movement_type,
                quantity=quantity,
            )
        )


def seed_demo_data() -> InMemoryDB:
    from datetime import date, timedelta

    from .domain import (
        MatchType,
        Member,
        PriceRule,
        PriceType,
        Product,
        ProductPackaging,
        RuleScope,
        StockBalance,
        Supplier,
        SupplierSKU,
    )

    now = datetime.now()
    db = InMemoryDB()

    db.products["P001"] = Product("P001", "康师傅红烧牛肉面 5连包", "Master Kong Beef Noodle 5pk", "食品", "方便面", "袋装")
    db.products["P002"] = Product("P002", "旺仔牛奶 245ml*24", "Want Want Milk 245ml*24", "饮料", "奶饮", "罐装")

    db.packaging.extend(
        [
            ProductPackaging("P001", "inner", 1, "6901234560011", 5.8),
            ProductPackaging("P001", "outer", 12, "6901234560012", 66.0),
            ProductPackaging("P002", "inner", 1, "6902234560011", 4.2, promo_price=3.9),
        ]
    )

    db.suppliers["S001"] = Supplier("S001", "亚洲食品供应商A", order_cycle_days=7)
    db.supplier_skus.extend(
        [SupplierSKU("P001", "S001", "A-NOODLE-001"), SupplierSKU("P002", "S001", "A-MILK-002")]
    )

    db.members["M001"] = Member("M001", "13800000000", "gold", birthday=date(1990, 8, 18))

    db.price_rules.extend(
        [
            PriceRule(
                id="R_MEMBER_PRODUCT",
                rule_scope=RuleScope.MEMBER,
                match_type=MatchType.EXACT_PRODUCT,
                match_value="P001",
                price_type=PriceType.FIXED_PRICE,
                value=5.2,
                priority=100,
                valid_from=now - timedelta(days=1),
                valid_to=now + timedelta(days=30),
                member_id="M001",
            ),
            PriceRule(
                id="R_TIER_CATEGORY",
                rule_scope=RuleScope.MEMBER_GROUP,
                match_type=MatchType.CATEGORY,
                match_value="饮料",
                price_type=PriceType.DISCOUNT_RATE,
                value=0.9,
                priority=50,
                valid_from=now - timedelta(days=1),
                valid_to=now + timedelta(days=30),
                member_tier="gold",
            ),
        ]
    )

    db.stock_balances.extend(
        [
            StockBalance("WH_SH_01", "P001", qty_on_hand=120, qty_reserved=20),
            StockBalance("WH_SH_01", "P002", qty_on_hand=35, qty_reserved=5),
        ]
    )
    return db
