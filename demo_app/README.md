# 亚洲食品超市 ERP 演示程序

这是一个**程序架构演示**（非生产系统），用纯 Python 展示你确认过的 MVP 核心能力：

- 商品/包装/供应商SKU
- 会员定价（不折上折，会员组价与活动价取 min）
- 采购补货建议计算
- 收货毛利率提醒
- 促销管理 + 自动生成促销价签任务
- 普通价签/补打价签队列

## 目录结构

```text
demo_app/
  src/erp_demo/
    domain.py         # 领域模型
    repositories.py   # 内存仓储 + 演示数据
    services.py       # 业务服务
    demo.py           # 终端演示入口
  tests/test_services.py
```

## 运行演示

```bash
PYTHONPATH=demo_app/src python -m erp_demo.demo
```

## 运行测试

```bash
PYTHONPATH=demo_app/src python -m unittest discover -s demo_app/tests -v
```

## 架构说明（简化版）

- `domain`：只放业务对象（Product、PriceRule、StockMovement...）。
- `repositories`：数据访问层（这里用内存实现，便于快速演示）。
- `services`：核心业务规则层：
  - `PricingService`：不折上折规则
  - `ReplenishmentService`：最小订货量/建议订货量
  - `ReceivingService`：毛利率计算与高亮标记
  - `PromotionService`：促销活动与促销价签队列
  - `LabelService`：正价签、补打队列
- `demo`：串联业务场景，方便你快速验收流程。
