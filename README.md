# Price Action Analysis Skill

Al Brooks 价格行为分析 Skill，用于 Claude Code。

## 功能

- 基于 Al Brooks 方法论的六层决策树（结构→方向→否决→信号→风险→入场）
- 支持美股(US)、港股(HK)、A股(CN) 市场，自动识别交易时段和午休
- 数据预处理脚本 (`preprocess.py`)：一次调用获取 EMA20、bar 分类、pattern 检测、ADR、micro channel、三推、摆动点等全部指标
- 市场时区感知：美股使用 US Eastern、港股/A股使用 UTC+8（不再依赖本地系统时钟）
- 紧凑输出：默认只返回今日 bars + 前日最后5根上下文，节省 ~40% token
- 加权否决评分（V9 ADR 分级计分 1-3 分，新增 V13 高潮否决）
- 震荡区间突破(TR-Breakout) 独立决策路径
- 简洁模式 (Template D)：快速输出分析结论

## 文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Skill 定义 — 决策树、模板、触发条件 |
| `preprocess.py` | 数据预处理 — EMA20, bar类型, pattern, session |

## 依赖

- [Futu OpenD](https://openapi.futunn.com/) 运行中 (默认 `127.0.0.1:11111`)
- Python 3.8+
- `futu-api` (pip install futu-api，自带 pandas)

## 使用

```bash
# 预处理数据（默认紧凑输出）
python preprocess.py "HK.800000"          # 恒生指数
python preprocess.py "HK.800700"          # 恒生科技
python preprocess.py "US.SPY"             # S&P 500 ETF
python preprocess.py "HK.800000" --full   # 输出全部80根bar

# 在 Claude Code 中触发
# 输入 /price-action 或直接问 "恒指现在怎么样"
```
