#!/usr/bin/env python3
"""Generate a clean professional Chinese resume PDF using ReportLab."""

from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ── Register CJK font ──────────────────────────────────────────────
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT = 'STSong-Light'

# ── Color palette ───────────────────────────────────────────────────
C_PRIMARY = HexColor('#1a2332')
C_BODY    = HexColor('#2d3436')
C_MUTED   = HexColor('#636e72')
C_ACCENT  = HexColor('#2563eb')
C_RULE    = HexColor('#d0d5dd')

# ── Page setup ──────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 22 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Styles ──────────────────────────────────────────────────────────
def make_style(name, **kw):
    defaults = dict(fontName=FONT, leading=16, spaceBefore=0, spaceAfter=0,
                    textColor=C_BODY, alignment=TA_LEFT)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

S_NAME      = make_style('Name', fontSize=26, leading=32, textColor=C_PRIMARY, spaceAfter=2)
S_SUBTITLE  = make_style('Subtitle', fontSize=11, leading=16, textColor=C_MUTED, spaceAfter=6)
S_SECTION   = make_style('Section', fontSize=14, leading=20, textColor=C_PRIMARY, spaceBefore=10, spaceAfter=4)
S_BODY      = make_style('Body', fontSize=10, leading=16, textColor=C_BODY)
S_DATE      = make_style('Date', fontSize=9.5, leading=14, textColor=C_MUTED, alignment=TA_RIGHT)
S_BULLET    = make_style('Bullet', fontSize=10, leading=17, textColor=C_BODY,
                          leftIndent=12, firstLineIndent=-6)

# ── Helpers ─────────────────────────────────────────────────────────
def hr():
    return HRFlowable(width="100%", thickness=0.5, color=C_RULE, spaceBefore=2, spaceAfter=6)

def section(title):
    return [Spacer(1, 6*mm), Paragraph(title, S_SECTION), hr()]

def bullet(text):
    return Paragraph(f'•  {text}', S_BULLET)

def link_paragraph(text, url):
    return Paragraph(
        f'{text}: <font color="{C_ACCENT.hexval()}"><u>{url}</u></font>',
        make_style('link', fontSize=9, leading=14, textColor=C_BODY)
    )

def work_entry(company, role, period, bullets, tags=None):
    items = []
    title_html = (
        f'<font color="{C_PRIMARY.hexval()}" size="12"><b>{company}</b></font>'
        f'&nbsp;&nbsp;&nbsp;'
        f'<font color="{C_BODY.hexval()}" size="10.5">{role}</font>'
    )
    t = Table(
        [[Paragraph(title_html, make_style('tmp', fontSize=11, leading=16)),
          Paragraph(period, S_DATE)]],
        colWidths=[CONTENT_W - 55*mm, 55*mm],
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    items.append(t)
    if tags:
        tag_str = '  |  '.join(
            f'<font color="{C_MUTED.hexval()}" size="9">{tag}</font>' for tag in tags
        )
        items.append(Paragraph(tag_str, make_style('tags', fontSize=9, leading=14,
                                                    spaceBefore=1, spaceAfter=2)))
    for b in bullets:
        items.append(bullet(b))
    items.append(Spacer(1, 4*mm))
    return items


# ══════════════════════════════════════════════════════════════════════
#  BUILD
# ══════════════════════════════════════════════════════════════════════

def build_story():
    story = []

    # ── Header ───────────────────────────────────────────────────────
    story.append(Paragraph('倪子尧', S_NAME))  # 倪子尧
    story.append(Paragraph(
        '前端工程师  ·  9 年经验  ·  1994.04',
        S_SUBTITLE
    ))  # 前端工程师 · 9 年经验 · 1994.04

    contact_html = (
        'GitHub: github.com/Nzy19940403'
        '  |  邮箱: [待补充]'
        '  |  手机: [待补充]'
        '  |  城市: [待补充]'
    )  # 邮箱/手机/城市
    story.append(Paragraph(
        f'<font color="{C_MUTED.hexval()}" size="9.5">{contact_html}</font>',
        make_style('contact', fontSize=9.5, leading=15, textColor=C_MUTED)
    ))
    story.append(Spacer(1, 3*mm))

    # ── 个人简介 ──────────────────────────────────────────────────────
    story.extend(section('个人简介'))
    story.append(Paragraph(
        '9 年前端开发经验，有 Geek 精神，对代码有追求，喜欢接触前沿技术。'
        '擅长复杂前端架构设计与工程化落地，在华为期间主导了盘古大模型工作台的微前端改造。'
        '近期独立研发了基于拓扑排序的响应式任务编排引擎 MeshFlow，'
        '并以此为基础配合 AI Agent 构建了 28+ 节点的面包店经营沙盘系统，'
        '完整验证了引擎在深度 DAG 依赖、冲突仲裁及多策略路线推演场景下的能力。',
        make_style('intro', fontSize=10, leading=17, textColor=C_BODY)
    ))

    # ── 个人开源项目 ──────────────────────────────────────────────────
    story.extend(section('个人开源项目'))  # 个人开源项目

    # MeshFlow
    proj_title = (
        f'<font color="{C_PRIMARY.hexval()}" size="12"><b>MeshFlow</b></font>'
        f' — '
        f'<font color="{C_BODY.hexval()}" size="10.5">高性能任务编排响应式引擎</font>'
    )  # — 高性能任务编排响应式引擎
    t = Table(
        [[Paragraph(proj_title, make_style('pt', fontSize=11, leading=16)),
          Paragraph('2025.11 – 至今', S_DATE)]],  # 至今
        colWidths=[CONTENT_W - 55*mm, 55*mm],
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t)

    story.append(link_paragraph('项目主页',
                                'https://github.com/Nzy19940403/meshflow'))
    story.append(link_paragraph('项目文档',
                                'https://meshflow-docs.nzyhave.fun/'))
    story.append(Spacer(1, 2*mm))

    story.append(bullet(
        '<b>因果确定性调度 (DAG)</b>：基于拓扑排序与水位线同步栅栏构建执行引擎，'
        '确保下游节点仅在所有依赖就绪后触发，杜绝中间态脏读与竞态覆盖。'
    ))
    story.append(bullet(
        '<b>任务版本覆盖机制 (Token)</b>：设计基于 Token 的状态保护标识，'
        '新任务序列始终拥有最高优先级，自动屏蔽过期异步回调，解决高频交互下的状态覆盖问题。'
    ))
    story.append(bullet(
        '<b>计算记忆化与拓扑剪枝</b>：基于依赖桶的结果快照机制，'
        '节点重计算结果与快照一致时自动阻断下游传播路径，拦截无效级联更新。'
    ))
    story.append(bullet(
        '<b>环路依赖治理 (纠缠机制)</b>：借鉴 CRDT 思想，引入 Ghost 权重仲裁将空间环路'
        '转化为时间轴线性演化，解决产能-成本等双向制约场景下的最终一致性收敛。'
    ))
    story.append(bullet(
        '<b>面包店经营沙盘 — 复杂系统实战验证</b>：配合 AI Agent 构建了含 28+ 节点、'
        '多层 DAG 依赖的面包店经营模拟系统。模型涵盖客流分化（常客/旅游客）、批发渠道自动触发、'
        '品质惩罚与品牌衰减、季节性波动、员工疲劳与经验累积等非线性机制；引擎在 SetRule 公式引擎、'
        '纠缠边（4条并行提案 + Ghost 仲裁）与衍生公式三者联动下，稳定推演出社区/大厂/高奢三条策略路线的差异化经营结果。'
    ))
    story.append(bullet(
        '<b>极致轻量</b>：压缩后仅 <b>13KB</b>，完全 Headless，无任何外部依赖。'
    ))
    story.append(Spacer(1, 4*mm))

    # ── 工作经历 ──────────────────────────────────────────────────────
    story.extend(section('工作经历'))

    # 创业
    story.extend(work_entry(
        company='创业项目（AIGC 方向）',
        role='联合创始人 / 前端负责人',
        period='2024.10 – 2025.06',
        tags=['AIGC', 'TTS', '创业'],
        bullets=[
            '与前华为同事联合创办 AIGC 方向产品公司，负责全部前端架构与开发工作。',
            '在项目期间探索了多个技术方向，包括独立搭建 VPN 服务、训练部署 txt2voice 语音合成模型等，拓展了全栈能力边界。',
        ]
    ))

    # 华为
    story.extend(work_entry(
        company='华为技术有限公司（华为云盘古大模型项目组）',
        role='前端工程师',
        period='2022.07 – 2024.10',
        tags=['微前端', 'Qiankun', 'Canvas', '大模型工程化'],
        bullets=[
            '<b>盘古大模型平台微前端改造（负责人）</b>：负责 Prompt 工程工作台的微前端架构设计，'
            '基于 Qiankun 实现模型训练、部署、评测等子应用的无缝集成。'
            '通过 externals 剥离公共依赖并集成 CDN 共享机制，将系统间切换白屏时间优化 40%。',
            '<b>盘古气象大模型可视化平台（核心开发）</b>：利用 Canvas 实现全球尺度高密度气象要素'
            '（风场、气压、降水）的高性能流体动画渲染。'
            '开发响应式 AI 推理交互页面，支持 Prompt 驱动气象参数调整与多模态对比展示。',
        ]
    ))

    # 光际科技
    story.extend(work_entry(
        company='上海光际科技有限公司',
        role='前端工程师',
        period='2017 – 2022.06',
        tags=['Angular', 'CVAT', '数据标注平台', 'TypeScript'],
        bullets=[
            '负责公司标注产品线的前端开发与维护，深度参与数据标注平台的架构设计与功能迭代。',
            '基于开源 CVAT（Computer Vision Annotation Tool）项目进行二次开发与定制，'
            '包括标注界面优化、工作流扩展、权限模块改造及标注格式适配，支撑日均万级标注任务处理。',
            '在 5 年任职期间从初级成长为团队前端核心，主导多个版本的升级与重构工作。',
        ]
    ))

    # ── 技能 ──────────────────────────────────────────────────────────
    story.extend(section('专业技能'))

    skill_groups = [
        ('Web 基础', 'HTML5 / CSS3、响应式布局、移动端适配、ES6+ / TypeScript'),
        ('框架 & 工具', 'Angular、Vue、Qiankun 微前端、Webpack / Vite 构建工具链'),
        ('数据可视化', 'Canvas API、高性能动画渲染、气象/地理数据可视化'),
        ('工程架构', '大型项目架构设计、微前端改造、DAG / 拓扑排序、任务编排引擎'),
        ('全栈 & DevOps', 'Node.js、TTS 模型训练与部署、VPN 服务搭建、Linux 运维'),
    ]

    skill_rows = []
    for cat, content in skill_groups:
        skill_rows.append([
            Paragraph(f'<font color="{C_PRIMARY.hexval()}" size="10"><b>{cat}</b></font>',
                      make_style('sk_cat', fontSize=10, leading=17)),
            Paragraph(f'<font color="{C_BODY.hexval()}" size="10">{content}</font>',
                      make_style('sk_val', fontSize=10, leading=17)),
        ])

    skill_table = Table(skill_rows, colWidths=[30*mm, CONTENT_W - 30*mm])
    skill_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(skill_table)

    # ── 教育背景 ──────────────────────────────────────────────────────
    story.extend(section('教育背景'))

    edu_html = (
        f'<font color="{C_PRIMARY.hexval()}" size="11"><b>合肥工业大学</b></font>'
        f'　　　'
        f'<font color="{C_BODY.hexval()}" size="10">能源与动力工程 · 本科</font>'
    )
    t = Table(
        [[Paragraph(edu_html, make_style('edu', fontSize=10.5, leading=16)),
          Paragraph('2012 – 2016', S_DATE)]],
        colWidths=[CONTENT_W - 55*mm, 55*mm],
    )
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t)

    return story


# ══════════════════════════════════════════════════════════════════════
output_path = '/sessions/lucid-gifted-ramanujan/mnt/meshflow-sheet/倪子尧_前端工程师_简历.pdf'

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    leftMargin=MARGIN,
    rightMargin=MARGIN,
    topMargin=18*mm,
    bottomMargin=18*mm,
    title='倪子尧 - 前端工程师简历',
    author='倪子尧',
)

story = build_story()
doc.build(story)
print(f'PDF saved to: {output_path}')
