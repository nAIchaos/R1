from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class RuleScope(str, Enum):
    MEMBER = "member"
    MEMBER_GROUP = "member_group"


class MatchType(str, Enum):
    EXACT_PRODUCT = "exact_product"
    CATEGORY = "category"


class PriceType(str, Enum):
    FIXED_PRICE = "fixed_price"
    DISCOUNT_RATE = "discount_rate"


@dataclass(slots=True)
class Product:
    id: str
    name_zh: str
    name_en: str
    category_lv1: str
    category_lv2: str
    category_lv3: str


@dataclass(slots=True)
class ProductPackaging:
    product_id: str
    pack_level: str  # inner/outer
    units_per_pack: int
    barcode: str
    list_price: float
    promo_price: Optional[float] = None
    promo_start_at: Optional[datetime] = None
    promo_end_at: Optional[datetime] = None


@dataclass(slots=True)
class Supplier:
    id: str
    name: str
    order_cycle_days: int


@dataclass(slots=True)
class SupplierSKU:
    product_id: str
    supplier_id: str
    supplier_sku: str
    enabled: bool = True


@dataclass(slots=True)
class Member:
    id: str
    mobile: str
    tier: str
    birthday: Optional[date] = None


@dataclass(slots=True)
class PriceRule:
    id: str
    rule_scope: RuleScope
    match_type: MatchType
    match_value: str
    price_type: PriceType
    value: float
    priority: int
    valid_from: datetime
    valid_to: datetime
    member_id: Optional[str] = None
    member_tier: Optional[str] = None


@dataclass(slots=True)
class StockBalance:
    warehouse_id: str
    product_id: str
    qty_on_hand: int
    qty_reserved: int
    latest_expiry_date: Optional[date] = None


@dataclass(slots=True)
class StockMovement:
    warehouse_id: str
    product_id: str
    movement_date: datetime
    movement_type: str
    quantity: int


@dataclass(slots=True)
class PromotionCampaign:
    id: str
    name: str
    campaign_type: str
    start_at: datetime
    end_at: datetime
    status: str


@dataclass(slots=True)
class PromotionItem:
    campaign_id: str
    product_id: str
    promo_price: Optional[float] = None
    discount_rate: Optional[float] = None


@dataclass(slots=True)
class LabelPrintLine:
    product_id: str
    pack_level: str
    price_to_print: float
    copies: int = 1


@dataclass(slots=True)
class LabelPrintTask:
    id: str
    task_type: str  # normal/promo/reprint
    lines: list[LabelPrintLine] = field(default_factory=list)
