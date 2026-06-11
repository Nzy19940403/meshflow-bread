#!/usr/bin/env python3
"""Modern two-column resume PDF."""

from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                 Paragraph, Spacer, Table, TableStyle, Flowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FN = 'STSong-Light'

BG_DARK   = HexColor('#1a2332')
C_WHITE   = HexColor('#ffffff')
C_ACCENT  = HexColor('#5b9bd5')
C_ACCENT2 = HexColor('#3a7bd5')
C_BODY    = HexColor('#2d3436')
C_MUTED   = HexColor('#636e72')
C_LIGHT   = HexColor('#b0b8c1')

PAGE_W, PAGE_H = A4
MARGIN    = 14*mm
SIDEBAR_W = 58*mm
GAP       = 10*mm
MAIN_X    = MARGIN + SIDEBAR_W + GAP
MAIN_W    = PAGE_W - MAIN_X - MARGIN

def S(name, **kw):
    d = dict(fontName=FN, leading=15, spaceBefore=0, spaceAfter=0,
             textColor=C_BODY, alignment=TA_LEFT)
    d.update(kw)
    return ParagraphStyle(name, **d)

class Bar(Flowable):
    def __init__(self, w, h=1.0*mm, color=C_ACCENT):
        Flowable.__init__(self)
        self.w, self.h, self.color = w, h, color
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.w, self.h, stroke=0, fill=1)
    def wrap(self, aw, ah):
        return (self.w, self.h + 2.5*mm)

def B(text, color=C_BODY, size=9.5):
    return Paragraph(
        '<font color="%s" size="%s">-  %s</font>' % (color.hexval(), size, text),
        S('b', fontSize=size, leading=size*1.7+0.5, textColor=color,
          leftIndent=10, firstLineIndent=-5)
    )

def draw_sidebar(canvas, doc):
    c = canvas
    c.saveState()
    c.setFillColor(BG_DARK)
    c.rect(0, 0, SIDEBAR_W + MARGIN, PAGE_H, stroke=0, fill=1)
    page_num = c.getPageNumber()
    if page_num > 1:
        c.restoreState()
        return
    top_y = PAGE_H - MARGIN - 5
    x0 = MARGIN + 5

    def sec_label(title, y):
        c.setFillColor(C_WHITE)
        c.setFont('STSong-Light', 11)
        c.drawString(x0, y, title)
        y -= 18
        c.setFillColor(HexColor('#3a5068'))
        c.rect(x0, y-2, 30, 0.6, stroke=0, fill=1)
        return y - 10

    y = top_y
    c.setFillColor(C_WHITE)
    c.setFont('STSong-Light', 22)
    c.drawString(x0, y, '倪子尧')
    y -= 30
    c.setFillColor(C_ACCENT)
    c.setFont('STSong-Light', 10)
    c.drawString(x0, y, 'Frontend Engineer')
    y -= 20

    y = sec_label('联系方式', y)
    contacts = [
        ('GitHub', 'github.com/Nzy19940403'),
        ('邮箱', 'nzy1994@outlook.com'),
        ('手机', '19532539335'),
        ('城市', '上海'),
    ]
    for label, value in contacts:
        c.setFillColor(C_LIGHT)
        c.setFont('STSong-Light', 8.5)
        c.drawString(x0, y, label)
        c.setFillColor(C_WHITE)
        c.setFont('STSong-Light', 9)
        c.drawString(x0 + 32, y, value)
        y -= 17

    y -= 5
    y = sec_label('专业技能', y)
    skills = ['HTML5 / CSS3', 'ES6+ / TypeScript', 'Angular', 'Vue',
              'Qiankun 微前端', 'Webpack / Vite']
    for s in skills:
        c.setFillColor(C_LIGHT)
        c.setFont('STSong-Light', 8.5)
        c.drawString(x0 + 4, y, s)
        y -= 15

    y -= 5
    y = sec_label('教育背景', y)
    c.setFillColor(C_WHITE)
    c.setFont('STSong-Light', 10)
    c.drawString(x0, y, '合肥工业大学')
    y -= 16
    c.setFillColor(C_LIGHT)
    c.setFont('STSong-Light', 9)
    c.drawString(x0, y, '能源与动力工程 · 本科')
    y -= 15
    c.setFillColor(C_MUTED)
    c.setFont('STSong-Light', 8.5)
    c.drawString(x0, y, '2012 — 2016')
    c.restoreState()


def section_header(title):
    return [
        Spacer(1, 5*mm),
        Paragraph('<font color="%s" size="13"><b>%s</b></font>' % (BG_DARK.hexval(), title),
                  S('sec', fontSize=13, leading=20, textColor=BG_DARK, spaceAfter=1)),
        Bar(MAIN_W, 1.2*mm, C_ACCENT),
        Spacer(1, 3*mm),
    ]


def work_block(company, role, period, bullets, tags=None):
    items = []
    t = Table([
        [Paragraph('<font size="11.5"><b>%s</b></font>' % company,
                   S('c1', fontSize=11.5, leading=17, textColor=BG_DARK)),
         Paragraph('<font color="%s" size="9">%s</font>' % (C_MUTED.hexval(), period),
                   S('d1', fontSize=9, leading=14, textColor=C_MUTED))],
    ], colWidths=[MAIN_W - 36*mm, 36*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    items.append(t)
    items.append(Paragraph(
        '<font color="%s" size="9.5">%s</font>' % (C_MUTED.hexval(), role),
        S('r1', fontSize=9.5, leading=15, textColor=C_MUTED, spaceAfter=1)))
    if tags:
        tag_text = '  ·  '.join(tags)
        items.append(Paragraph(
            '<font color="%s" size="8.5">%s</font>' % (C_ACCENT2.hexval(), tag_text),
            S('t1', fontSize=8.5, leading=14, textColor=C_ACCENT2, spaceAfter=2)))
    for b in bullets:
        items.append(B(b))
    items.append(Spacer(1, 3.5*mm))
    return items


def proj_title(items, title, subtitle, period):
    items.append(Paragraph(
        '<font size="12"><b>%s</b></font>' % title,
        S('pj', fontSize=12, leading=18, textColor=BG_DARK, spaceAfter=0)))
    items.append(Paragraph(
        '<font color="%s" size="10">%s</font>' % (C_MUTED.hexval(), subtitle),
        S('pjsub', fontSize=10, leading=16, textColor=C_MUTED, spaceAfter=1)))
    items.append(Paragraph(
        '<font color="%s" size="8.5">%s</font>' % (C_MUTED.hexval(), period),
        S('pjl', fontSize=8.5, leading=14, textColor=C_MUTED, spaceAfter=1)))

def proj_link(items, text, url):
    items.append(Paragraph(
        '<font color="%s" size="8.5">%s</font>  '
        '<font color="%s" size="8.5">%s</font>' % (C_MUTED.hexval(), text, C_ACCENT2.hexval(), url),
        S('pjl', fontSize=8.5, leading=14, textColor=C_MUTED, spaceAfter=0)))


def build_main():
    items = []

    items.extend(section_header('个人概况'))
    items.append(Paragraph(
        '喜欢编码，爱折腾，'
        '喜欢接触前沿技术。'
        '独立研发了 13KB 的任务编排引擎 MeshFlow，'
        '并用其构建了面包店经营沙盘作为实战验证。',
        S('sum', fontSize=9.5, leading=17, textColor=C_BODY)
    ))

    items.extend(section_header('个人开源项目'))

    # MeshFlow
    proj_title(items, 'MeshFlow',
               '高性能任务编排响应式引擎',
               '2025.11 — 至今')
    proj_link(items, 'GitHub:', 'github.com/Nzy19940403/meshflow')
    proj_link(items, '文档:', 'meshflow-docs.nzyhave.fun')
    items.append(Spacer(1, 1*mm))

    meshflow_bullets = [
        '<b>因果确定性调度 (DAG)</b>：'
        '基于拓扑排序与水位线同步栅栏构建执行引擎，'
        '确保下游节点仅在所有依赖就绪后触发，'
        '杜绝中间态脏读。',
        '<b>任务版本覆盖 (Token)</b>：'
        '设计 Token 状态保护标识，'
        '新任务始终拥有最高优先级，'
        '自动屏蔽过期异步回调，'
        '解决高频交互下的竞态覆盖。',
        '<b>计算记忆化与拓扑剪枝</b>：'
        '基于依赖桶的结果快照，'
        '节点重计算结果一致时自动阻断下游传播路径，'
        '拦截无效级联更新。',
        '<b>环路依赖治理 (纠缠机制)</b>：'
        '借鉴 CRDT 思想，引入 Ghost 权重仲裁将空间环路转为'
        '时间轴线性演化，确保双向制约场景下的最终一致性收敛。',
        '<b>极致轻量</b>：压缩后仅 13KB，完全 Headless，零外部依赖。',
    ]
    for txt in meshflow_bullets:
        clr = C_MUTED if '极致轻量' in txt else C_BODY
        items.append(B(txt, clr))

    items.append(Spacer(1, 6*mm))

    # Bakery divider
    items.append(Bar(MAIN_W * 0.4, 0.4*mm, HexColor('#d0d5dd')))
    items.append(Spacer(1, 3*mm))

    proj_title(items, '面包店经营沙盘',
               'MeshFlow 复杂系统实战验证',
               '2026.06')
    proj_link(items, 'Demo:', 'meshflow-bread.vercel.app')
    items.append(Spacer(1, 1*mm))

    bakery_bullets = [
        '22 个节点之间不仅存在单向 DAG 数据流，'
        '还包含循环依赖——'
        '例如产能影响加工成本、加工成本又反过来影响产能，'
        '形成闭环。这种链路无法用传统拓扑排序处理，'
        '必须依赖引擎的纠缠机制进行冲突仲裁与收敛。',
        '模型涵盖客流分化、批发渠道自动触发、品质惩罚与品牌衰减、'
        '季节性波动等非线性机制。',
        '支持社区/大厂/高奢三条策略路线的差异化推演。',
        '配合 AI 辅助完成前端开发与 Python 穷举验证，'
        '现已部署上线并提供 DAG 节点依赖关系视图。',
    ]
    for txt in bakery_bullets:
        items.append(B(txt))

    # Work
    items.extend(section_header('工作经历'))

    items.extend(work_block(
        '创业项目（AIGC 方向）',
        '联合创始人 / 前端负责人',
        '2024.10 — 2025.06',
        [
            '与前华为同事联合创办 AIGC 方向产品公司，'
            '负责前端架构与开发。',
            '参与 txt2voice 语音合成模型的训练工作，'
            '了解数据采集、标注与模型训练的基本流程。',
        ],
        tags=['AIGC', '创业']
    ))

    items.extend(work_block(
        '华为技术有限公司 · 华为云盘古大模型项目组',
        '前端工程师',
        '2022.07 — 2024.10',
        [
            '<b>盘古大模型平台微前端改造（负责人）</b>：'
            '基于 Qiankun 实现模型训练、部署、评测等子应用的无缝集成，'
            '通过 CSS 隔离与 JS 沙箱机制确保子应用独立运行；'
            '利用 externals 剥离公共依赖并集成 CDN 共享机制，'
            '系统间切换白屏时间优化 40%。',
            '<b>盘古气象大模型可视化平台（核心开发）</b>：'
            '利用 Canvas 实现全球尺度高密度气象要素'
            '（风场、气压、降水）的高性能流体动画渲染，'
            '支持气象预测结果的实时可视化对比与交互分析。',
        ],
        tags=['微前端', 'Qiankun', 'Canvas']
    ))

    items.extend(work_block(
        '上海光际科技有限公司',
        '前端工程师',
        '2017 — 2022.06',
        [
            '负责公司标注产品线前端开发与维护，'
            '深度参与数据标注平台的架构设计与功能迭代。',
            '基于开源 CVAT（Computer Vision Annotation Tool）项目进行二次开发与定制，'
            '包括标注界面优化、工作流扩展、权限模块改造及标注格式适配，'
            '支撑日均万级标注任务处理。',
            '5 年期间从初级成长为团队前端核心，'
            '主导多个版本升级与重构。',
        ],
        tags=['Angular', 'CVAT', 'TypeScript']
    ))

    return items


output_path = '/sessions/lucid-gifted-ramanujan/mnt/meshflow-sheet/resume.pdf'

class ResumeDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        main_frame = Frame(MAIN_X, MARGIN, MAIN_W, PAGE_H - MARGIN*2, id='main')
        self.addPageTemplates([PageTemplate(id='R', frames=[main_frame], onPage=draw_sidebar)])

doc = ResumeDoc(output_path, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0,
                title='Resume', author='Nzy')
doc.build(build_main())
print('Done')
