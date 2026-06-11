// 面包店经营模型节点情报 — 逐节点对照 V8 引擎实际 SetRule/Entangle
// 每条记录：节点名、图标、业务解释、上游(影响因素)、下游(受波及节点)

export interface NodeInfo {
  icon: string
  name: string
  desc: string
  inputs: string[]
  outputs: string[]
}

export const NODE_INFO: Record<string, NodeInfo> = {
  // ===== 可编辑滑块 =====
  B1:  { icon: '💰', name: '售价',     desc: '零售单价。涨价→单件利润高但转化率降, 降价→薄利多销。工厂B2B价=min(售价,¥22)×25%。', inputs: [],              outputs: ['B2','B6','B7'] },
  B10: { icon: '🥖', name: '原料成本', desc: '每件原料单价¥1-6。低价→成品成本低但品质B28差→品牌涨不动且B2B被压价。',                inputs: [],              outputs: ['B12','B28'] },
  B13: { icon: '📢', name: '营销投入', desc: '每月广告推广预算。吸引客流(√递减), 同时提升品牌知名度。工厂B2B占比高时可砍掉。',        inputs: [],              outputs: ['B2','B7','BRAND'] },
  B14: { icon: '📐', name: '店面面积', desc: 'm²。面积↑→产能↑+店面可见度↑→客流↑。≥150m²触发B2B。但租金和折旧也涨。',               inputs: [],              outputs: ['B3','B5','B2'] },
  B15: { icon: '⭐', name: '场地等级', desc: '商圈繁华度1-10。等级↑→客流↑+房租↑+品牌溢价权限↑。≥5触发旅游客流。',                 inputs: [],              outputs: ['B2','B5','B9','B21'] },
  B24: { icon: '👥', name: '员工数',   desc: '全职人数。人多→产能↑+B2B量↑。但人工成本和管理复杂度也涨。',                            inputs: [],              outputs: ['B3','B9'] },
  B25: { icon: '📚', name: '培训投入', desc: '每月人均培训预算。直接计入B8固定成本。B8的trn=B25×B24。',                               inputs: [],              outputs: ['B8'] },
  B26: { icon: '💵', name: '基础工资', desc: '每人月薪¥800-10k。高薪→满意度↑+废品率↓+品质微提+ma上限↑。低薪→满意度跌。',          inputs: [],              outputs: ['B2','B4','B9','B21','B28'] },

  // ===== 中间计算层 =====
  B9:  { icon: '👷', name: '人工成本', desc: '月人工总额 = 员工×工资×(1+地段×0.10×管理衰减)。',                                      inputs: ['B24','B26','B15'], outputs: ['B7','B21'] },
  B3:  { icon: '🏭', name: '月产能',   desc: 'min(面积×apm, 人数×spm)×sk(FAT)。产能上限受面积或人工短板限制, FAT>80后断崖下跌。',      inputs: ['B14','B24','FAT','B4'], outputs: ['B4','B6','B12','B21'] },
  B4:  { icon: '🔧', name: '加工成本', desc: '每件加工费。产能↑→规模效应降本。高薪→低废品率→进一步降本。下限¥0.03。',                inputs: ['B3','B26'],     outputs: ['B3','B12'] },
  B28: { icon: '🧪', name: '原料品质', desc: '0-1评分。B10/5.5定基础+高薪(B26>3k)引好师傅微提。品质<0.4→品牌天花板锁死25→B2B打7折。', inputs: ['B10','B26'],    outputs: ['B2','B7','B20','BRAND'] },
  FAT: { icon: '⚡', name: '疲劳',     desc: '0-100。零售UR>88%→+40/月。B2B总UR>65%→+15/月。UR≥90%禁止恢复。<65%才恢复。',          inputs: ['B2','B3'],       outputs: ['B3','B21','BRAND'] },
  B21: { icon: '😊', name: '满意度',   desc: '工资×0.4+产出效率×0.6-过劳。高薪+合理负荷=高满意。FAT>60开始侵蚀(0.004/点)。',         inputs: ['B3','B9','B15','B26','FAT'], outputs: ['B2','B20','BRAND'] },
  B20: { icon: '😋', name: '口味/品质', desc: '面包成品评分 = B21满意度×0.45 + B28原料品质×0.55。好师傅+好原料=好面包。',                inputs: ['B21','B28'],     outputs: ['BRAND'] },

  // ===== 市场与客流 =====
  B2:  { icon: '📊', name: '零售需求', desc: '客流(地段/面积/营销/口碑)×转化率(价格/品牌/满意/品质)×季节系数。',                    inputs: ['B1','B13','B14','B15','B21','B26','B28','BRAND'], outputs: ['B6','FAT','BRAND'] },
  BRAND: { icon: '🌟', name: '品牌知名度', desc: '增长=口味B20+满意B21+品质B28+营销B13+疲劳修正(100-FAT)/100×5。每月衰减1.5%。缺货(B2)扣8点。', inputs: ['B13','B20','B21','B28','B2','FAT'], outputs: ['B2'] },

  // ===== 财务汇总 =====
  B5:  { icon: '🏢', name: '房租',     desc: '面积×地段×动态单价(rb+rd/(area+15))。工业区(低地段)租金极便宜, 核心商圈极贵。',       inputs: ['B14','B15'],    outputs: ['B7'] },
  B12: { icon: '🏗️', name: '实际原料成本', desc: 'B10×(1-min(0.4,B3×0.00006))。批量采购折扣, 产能越高越便宜。上限40%折扣。',        inputs: ['B10','B3'],     outputs: ['B7'] },
  B6:  { icon: '📦', name: '零售销量', desc: '实际零售出货 = min(需求B2, 产能B3)。卖多少取决于"想要多少"和"能做多少"的短板。',         inputs: ['B2','B3'], outputs: ['B7','B8'] },
  B7:  { icon: '📈', name: '月收入',   desc: '零售收入 = 销量(B6) × 售价(B1)。',         inputs: ['B1','B6'], outputs: ['B8'] },
  B2B: { icon: '🚛', name: '批发销量', desc: '工厂路线专属: 面积≥150㎡时剩余产能全部走B2B企业订单。每人月出1200件+超额㎡×500件。社区/高奢此值为0。', inputs: ['B14','B3','B6','B24'], outputs: ['B7','COST'] },
  COST:{ icon: '💸', name: '总成本',   desc: '所有成本项汇总: 零售COGS+批发COGS+房租+人工+营销+培训+折旧+水电。', inputs: ['B12','B1','B4','B5','B9','B24','B25','B13','B14','B6','B2B','B10'], outputs: ['B8'] },
  B8:  { icon: '✅', name: '月利润',   desc: 'B7月收入 − COST总成本。正=盈利, 负=亏损。', inputs: ['B7','COST'], outputs: [] },
}
