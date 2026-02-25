from __future__ import annotations

import unittest

from erp_demo.domain import PromotionCampaign, PromotionItem
from erp_demo.repositories import seed_demo_data
from erp_demo.services import LabelService, PricingService, ReplenishmentInput, ReplenishmentService, PromotionService


class TestServices(unittest.TestCase):
    def setUp(self) -> None:
        self.db = seed_demo_data()

    def test_pricing_non_stacking(self):
        svc = PricingService(self.db)
        # P002 list=4.2, promo=3.9, gold category discount=0.9 => 3.78; take min(group,promo)
        self.assertEqual(svc.final_price("M001", "P002"), 3.78)

    def test_replenishment(self):
        svc = ReplenishmentService()
        result = svc.suggest_order(
            ReplenishmentInput(
                avg_daily_sales_30d=5,
                max_daily_sales_30d=8,
                cycle_days=7,
                on_hand=20,
                reserved=5,
                in_transit=0,
                safety_days=7,
                last_order_qty=40,
            )
        )
        self.assertGreaterEqual(result["suggest_order_qty"], result["min_order_qty"])

    def test_label_queues(self):
        svc = LabelService(self.db)
        normal = svc.queue_new_product_label("P001")
        self.assertGreaterEqual(len(normal.lines), 1)
        reprint = svc.queue_reprint_by_barcode_or_sku("A-NOODLE-001")
        self.assertGreaterEqual(len(reprint.lines), 1)

    def test_promotion_label_generation(self):
        promo = PromotionService(self.db)
        camp = PromotionCampaign(
            id="C1",
            name="test",
            campaign_type="single",
            start_at=__import__("datetime").datetime.now(),
            end_at=__import__("datetime").datetime.now(),
            status="active",
        )
        promo.create_campaign(camp, [PromotionItem(campaign_id="C1", product_id="P002", promo_price=3.5)])
        task = promo.generate_promo_label_task("C1")
        self.assertEqual(task.task_type, "promo")
        self.assertEqual(task.lines[0].price_to_print, 3.5)


if __name__ == "__main__":
    unittest.main()
