from __future__ import annotations

from datetime import datetime, timedelta

from .domain import PromotionCampaign, PromotionItem
from .repositories import seed_demo_data
from .services import (
    LabelService,
    PricingService,
    ReceivingService,
    ReplenishmentInput,
    ReplenishmentService,
    PromotionService,
)


def run_demo() -> None:
    db = seed_demo_data()

    pricing = PricingService(db)
    replenish = ReplenishmentService()
    receiving = ReceivingService(db)
    promo = PromotionService(db)
    label = LabelService(db)

    print("=== 1) 会员定价（不折上折）===")
    final_price = pricing.final_price(member_id="M001", product_id="P002", pack_level="inner")
    print(f"会员 M001 购买 P002 内包装最终价: {final_price}")

    print("\n=== 2) 自动补货建议 ===")
    suggestion = replenish.suggest_order(
        ReplenishmentInput(
            avg_daily_sales_30d=5.5,
            max_daily_sales_30d=9.0,
            cycle_days=7,
            on_hand=35,
            reserved=5,
            in_transit=0,
            last_order_qty=40,
        )
    )
    print(suggestion)

    print("\n=== 3) 收货毛利率提示 ===")
    margin = receiving.gross_margin(sale_price=4.2, purchase_price=3.95)
    flag = receiving.margin_flag(sale_price=4.2, purchase_price=3.95)
    print(f"本次毛利率: {margin:.2%}, 标记: {flag}")

    print("\n=== 4) 促销创建并自动生成特价签 ===")
    campaign = PromotionCampaign(
        id="CAMP-001",
        name="饮料周末促销",
        campaign_type="category_discount",
        start_at=datetime.now(),
        end_at=datetime.now() + timedelta(days=2),
        status="active",
    )
    promo.create_campaign(campaign, [PromotionItem(campaign_id="CAMP-001", product_id="P002", promo_price=3.6)])
    task = promo.generate_promo_label_task("CAMP-001")
    print(f"促销价签任务: {task.id}, 行数: {len(task.lines)}")

    print("\n=== 5) 新商品/补打价签 ===")
    normal = label.queue_new_product_label("P001")
    reprint = label.queue_reprint_by_barcode_or_sku("A-NOODLE-001")
    print(f"普通价签任务行数: {len(normal.lines)}; 补打任务行数: {len(reprint.lines)}")

    print("\n注：演示程序默认采用 A4 七行三列模板逻辑（模板细节由前端打印模块实现）。")


if __name__ == "__main__":
    run_demo()
