* 设置图形默认字体（需系统已安装对应字体）
graph set window fontface "SimSun"
graph set window fontface "Times New Roman"
graph set eps fontface "Times New Roman"


//两阶段残差回归
//性别
*添加值标签
rename 服务人员性别 窗口服务人员性别
rename 公众性别数字 办事公众性别

label define public_gender_label1 1 "办事公众：男性" 2 "办事公众：女性"
label values 办事公众性别 public_gender_label1

label define staff_gender_label1 1 "窗口服务人员：男性" 2 "窗口服务人员：女性"
label values 窗口服务人员性别 staff_gender_label1

*1.第一阶段回归
drop resid_sat res extreme
reghdfe 公众整体满意度 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 , absorb(服务大厅所在区 服务大厅类型 B) vce(cluster 服务大厅所在区)  resid(resid_sat)

*2.残差诊断
predict res, residual
*Q-Q图
qnorm res
*直方图
hist res
*描述性统计
sum res, detail

* 标记残差绝对值大于3倍标准差的样本
 // 3σ原则
gen extreme = (abs(res) > 3*0.6349)
 // 查看极端值比例，若<5%可直接删除
tab extreme 
list 公众整体满意度 办事公众性别 窗口服务人员性别 if extreme  // 检查原始数据是否合理

*3.第二阶段回归
* 方案1：不删除极端值（原模型）
reg resid_sat i.窗口服务人员性别##i.办事公众性别 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围, vce(cluster 服务大厅所在区)
estimates store model_性别
* 方案2：删除极端值
reg resid_sat i.窗口服务人员性别##i.办事公众性别 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 if !extreme, vce(cluster 服务大厅所在区)
* 导出
esttab model_性别 using "第二阶段回归_性别.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：标准误聚类在服务大厅层面；括号内为t值。")

*4.边际效应
margins i.窗口服务人员性别##i.办事公众性别, atmeans post
estimates store model_性别边际效应
* 导出
esttab model_性别边际效应 using "第二阶段回归_性别边际效应.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：括号内为t值。")

*画图  
marginsplot, xdim(窗口服务人员性别) plotdim(办事公众性别) ciopts(lcolor(black*0.5) lpattern(dash) ) plot1opts(lpattern(solid) msymbol(i)) plot2opts(lpattern(dash_dot) msymbol(i) ) plot3opts(lpattern(longdash) msymbol(i)) graphregion(color(white)) level(90) title("不同性别组合的边际效应") xtitle("窗口服务人员性别")  ytitle("政务服务净满意度") xlabel(#2 1"男性" 2"女性",tposition(inside))  ylabel(-0.1 "-0.1" 0 "0" 0.1 "0.1" 0.2 "0.2" ,tposition(inside) nogrid)  legend( size(small) row(1) region(lcolor(white) fcolor(white))) 
*导出
graph export "D:\搞学术\5数字政府1\数据\marginsplot_性别.png", width(1200) height(800) replace 

* 5. 假设检验
*男服务对不同性别公众差异
test 1.窗口服务人员性别#1.办事公众性别 = 1.窗口服务人员性别#2.办事公众性别
*女服务对不同性别公众差异
test 2.窗口服务人员性别#1.办事公众性别 = 2.窗口服务人员性别#2.办事公众性别
*女vs男服务对女公众
lincom 2.窗口服务人员性别#2.办事公众性别 - 1.窗口服务人员性别#2.办事公众性别









//代际差异
*添加值标签
label define public_age_label3 1 "办事公众：青年组" 2 "办事公众：壮年组" 3 "办事公众：实年组"
label values 办事公众年龄 public_age_label3

label define staff_age_label3 1 "服务人员：青年组" 2 "服务人员：壮年组" 3 "服务人员：实年组"
label values 窗口服务人员年龄 staff_age_label3

*1.第一阶段回归
drop resid_sat res extreme
reghdfe 公众整体满意度 办事公众性别 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 , absorb(服务大厅所在区 服务大厅类型 B) vce(cluster 服务大厅所在区)  resid(resid_sat)

*2.残差诊断
predict res, residual
*Q-Q图
qnorm res
*直方图
hist res
*描述性统计
sum res, detail

* 标记残差绝对值大于3倍标准差的样本
 // 3σ原则
gen extreme = (abs(res) > 3*0.6349)
 // 查看极端值比例，若<5%可直接删除
tab extreme 
list 公众整体满意度 办事公众性别 窗口服务人员性别 if extreme  // 检查原始数据是否合理

*3.第二阶段回归
* 方案1：不删除极端值（原模型）
reg resid_sat i.窗口服务人员年龄##i.办事公众年龄 办事公众性别 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围, vce(cluster 服务大厅所在区)
estimates store model_代际
* 方案2：删除极端值
reg resid_sat  i.窗口服务人员年龄##i.办事公众年龄 办事公众性别 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 if !extreme, vce(cluster 服务大厅所在区)
estimates store model_no_extreme
* 对比交互项系数// 仅展示交互项
estimates table model_full model_no_extreme, keep(*#*)  
* 导出
esttab model_代际 using "第二阶段回归_代际.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：标准误聚类在服务大厅层面；括号内为t值。")

*4.边际效应
margins i.窗口服务人员年龄##i.办事公众年龄, atmeans
* 导出
esttab model_性别边际效应 using "第二阶段回归_性别边际效应.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：括号内为t值。")

*画图  
marginsplot, xdim(窗口服务人员年龄) plotdim(办事公众年龄) ciopts(lcolor(black*0.5) lpattern(dash) ) plot1opts(lpattern(solid) msymbol(i)) plot2opts(lpattern(dash_dot) msymbol(i) ) plot3opts(lpattern(longdash) msymbol(i)) graphregion(color(white)) level(90) title("不同年龄组合的边际效应") xtitle("窗口服务人员年龄")  ytitle("政务服务净满意度") xlabel(#2 1"青年组" 2"壮年组",tposition(inside))  ylabel(-0.1 "-0.1" 0 "0" 0.1 "0.1" 0.2 "0.2" ,tposition(inside) nogrid)  legend( size(small) row(1) region(lcolor(white) fcolor(white))) 
*导出
graph export "D:\搞学术\5数字政府1\数据\marginsplot_代际.png", width(1200) height(800) replace 




//受教育水平差异
*1.第一阶段回归
drop resid_sat res extreme
reghdfe 公众整体满意度 办事公众性别 公众年龄 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 , absorb(服务大厅所在区 服务大厅类型 B) vce(cluster 服务大厅所在区)  resid(resid_sat)

*2.残差诊断
predict res, residual
*Q-Q图
qnorm res
*直方图
hist res
*描述性统计
sum res, detail

* 标记残差绝对值大于3倍标准差的样本
 // 3σ原则
gen extreme = (abs(res) > 3*0.6349)
 // 查看极端值比例，若<5%可直接删除
tab extreme 
list 公众整体满意度 办事公众性别 窗口服务人员性别 if extreme  // 检查原始数据是否合理

*3.第二阶段回归
* 方案1：不删除极端值（原模型）
reg resid_sat i.服务人员最高受教育程度##i.公众最高受教育程度 办事公众性别 窗口服务人员性别 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围, vce(cluster 服务大厅所在区)
estimates store model_学历
* 方案2：删除极端值
reg resid_sat  i.服务人员最高受教育程度##i.公众最高受教育程度 办事公众性别 窗口服务人员性别  公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 if !extreme, vce(cluster 服务大厅所在区)
estimates store model_no_extreme

* 导出
esttab model_学历 using "第二阶段回归_学历.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：标准误聚类在服务大厅层面；括号内为t值。")

*4.边际效应
margins i.服务人员最高受教育程度##i.公众最高受教育程度, atmeans
* 导出
esttab model_学历边际效应 using "第二阶段回归_学历边际效应.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：括号内为t值。")

*画图  
marginsplot, xdim(服务人员最高受教育程度) plotdim(公众最高受教育程度) ciopts(lcolor(black*0.5) lpattern(dash) ) plot1opts(lpattern(solid) msymbol(i)) plot2opts(lpattern(dash_dot) msymbol(i) ) plot3opts(lpattern(longdash) msymbol(i)) plot4opts(lpattern(dash) msymbol(i)) plot5opts(lpattern(dot) msymbol(i)) graphregion(color(white)) level(90) title("不同学历组合的边际效应") xtitle("窗口服务人员学历")  ytitle("政务服务净满意度") xlabel(#2 3"高中" 4"大学" 5"研究生", tposition(inside))  ylabel(-0.1 "-0.1" 0 "0" 0.1 "0.1" 0.2 "0.2" ,tposition(inside) nogrid)  legend( size(small) region(lcolor(white) fcolor(white))) 
*导出
graph export "D:\搞学术\5数字政府1\数据\marginsplot_学历.png", width(1200) height(800) replace 






//同乡
*更换为数字
* 方法：使用replace命令直接修改原变量
replace 公众户籍 = "1" if 公众户籍 == "北京"
replace 公众户籍 = "2" if 公众户籍 == "天津"
replace 公众户籍 = "3" if 公众户籍 == "河北"
replace 公众户籍 = "4" if 公众户籍 == "山西"
replace 公众户籍 = "5" if 公众户籍 == "内蒙古"
replace 公众户籍 = "6" if 公众户籍 == "辽宁"
replace 公众户籍 = "7" if 公众户籍 == "吉林"
replace 公众户籍 = "8" if 公众户籍 == "黑龙江"
replace 公众户籍 = "9" if 公众户籍 == "上海"
replace 公众户籍 = "10" if 公众户籍 == "江苏"
replace 公众户籍 = "11" if 公众户籍 == "浙江"
replace 公众户籍 = "12" if 公众户籍 == "安徽"
replace 公众户籍 = "13" if 公众户籍 == "福建"
replace 公众户籍 = "14" if 公众户籍 == "江西"
replace 公众户籍 = "15" if 公众户籍 == "山东"
replace 公众户籍 = "16" if 公众户籍 == "河南"
replace 公众户籍 = "17" if 公众户籍 == "湖北"
replace 公众户籍 = "18" if 公众户籍 == "湖南"
replace 公众户籍 = "19" if 公众户籍 == "广东"
replace 公众户籍 = "20" if 公众户籍 == "广西"
replace 公众户籍 = "21" if 公众户籍 == "海南"
replace 公众户籍 = "22" if 公众户籍 == "重庆"
replace 公众户籍 = "23" if 公众户籍 == "四川"
replace 公众户籍 = "24" if 公众户籍 == "贵州"
replace 公众户籍 = "25" if 公众户籍 == "云南"
replace 公众户籍 = "26" if 公众户籍 == "西藏"
replace 公众户籍 = "27" if 公众户籍 == "陕西"
replace 公众户籍 = "28" if 公众户籍 == "甘肃"
replace 公众户籍 = "29" if 公众户籍 == "青海"
replace 公众户籍 = "30" if 公众户籍 == "宁夏"
replace 公众户籍 = "31" if 公众户籍 == "新疆"
replace 公众户籍 = "32" if 公众户籍 == "台湾"
replace 公众户籍 = "33" if 公众户籍 == "香港"
replace 公众户籍 = "34" if 公众户籍 == "澳门"
replace 公众户籍 = "35" if 公众户籍 == "海外"
* 将变量类型从字符串转为数值
destring 公众户籍, replace

*1.第一阶段回归
drop resid_sat res extreme
reghdfe 公众整体满意度 办事公众性别 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 , absorb(服务大厅所在区 服务大厅类型 B) vce(cluster 服务大厅所在区)  resid(resid_sat)

*2.残差诊断
predict res, residual
*Q-Q图
qnorm res
*直方图
hist res
*描述性统计
sum res, detail

* 标记残差绝对值大于3倍标准差的样本
 // 3σ原则
gen extreme = (abs(res) > 3*0.6349)
 // 查看极端值比例，若<5%可直接删除
tab extreme 
list 公众整体满意度 办事公众性别 窗口服务人员性别 if extreme  // 检查原始数据是否合理

*3.第二阶段回归
* 方案1：不删除极端值（原模型）
reg resid_sat i.服务人员籍贯##i.公众户籍 办事公众性别 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围, vce(cluster 服务大厅所在区)
estimates store model_户籍
* 方案2：删除极端值
reg resid_sat i.服务人员籍贯##i.公众户籍 办事公众性别 公众年龄 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 if !extreme, vce(cluster 服务大厅所在区)
* 导出
esttab model_户籍 using "第二阶段回归_户籍.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：标准误聚类在服务大厅层面；括号内为t值。")

*4.边际效应
margins i.服务人员籍贯##i.公众户籍, atmeans post
*2、5、6、10、14、16、23、24、25、27
margins i.服务人员籍贯##i.公众户籍 if (公众户籍 == 服务人员籍贯) & (公众户籍==2 | 公众户籍==5 | 公众户籍==6 | 公众户籍==10 | 公众户籍==14 | 公众户籍==16 | 公众户籍==23 | 公众户籍==24  | 公众户籍==25 | 公众户籍==27), atmeans post
estimates store model_户籍边际效应
* 导出
esttab model_户籍边际效应 using "第二阶段回归_户籍边际效应.rtf", replace b(4) t(4) nonum nomti scalars(N r2_a) star(* 0.1 ** 0.05 *** 0.01)  addnotes("注：括号内为t值。")

*画图  
marginsplot, xdim(服务人员籍贯) plotdim(公众户籍) ciopts(lcolor(black*0.5) lpattern(dash) ) plot1opts(lpattern(solid) msymbol(i)) plot2opts(lpattern(dash_dot) msymbol(i) ) plot3opts(lpattern(longdash) msymbol(i)) graphregion(color(white)) level(90) title("同乡组合的边际效应") xtitle("窗口服务人员户籍")  ytitle("政务服务净满意度") xlabel( #2 2 5 6 10 14 16 23 24 25 27,tposition(inside))  ylabel(-1 "-1" -0.5 "-0.5" 0 "0" 0.5 "0.5" 1 "1" ,tposition(inside) nogrid)  legend( size(small) row(3) region(lcolor(white) fcolor(white))) 
*导出
graph export "D:\搞学术\5数字政府1\数据\marginsplot_户籍.png", width(1200) height(800) replace 



//多属性交叉
*1.第一阶段回归
drop resid_sat res extreme
reghdfe 公众整体满意度 公众最高受教育程度是 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围 , absorb(服务大厅所在区 服务大厅类型 B) vce(cluster 服务大厅所在区)  resid(resid_sat)

*2.残差诊断
predict res, residual
*Q-Q图
qnorm res
*直方图
hist res
*描述性统计
sum res, detail
* 标记残差绝对值大于3倍标准差的样本
 // 3σ原则
gen extreme = (abs(res) > 3*0.6349)
 // 查看极端值比例，若<5%可直接删除
tab extreme 
list 公众整体满意度 办事公众性别 窗口服务人员性别 if extreme  // 检查原始数据是否合理

*3.第二阶段回归
reg resid_sat i.窗口服务人员年龄##i.办事公众年龄##i.办事公众性别##i.窗口服务人员性别 公众事前对服务质量的预期较好 公众具有办事经验对办事过程比较熟悉 公众生活满意度 公众听普通话能力 公众说普通话能力 公众听英语能力 公众说英语能力 审批成功1 材料数量复杂度 公众遇到的其他前来办事的公众的数量和密度没有很大在可接受范围, vce(cluster 服务大厅所在区)


这个模型真的存在吗，找参考文献；
如果需要两阶段控制变量一致，固定效应是不是也应该一致；
缺点：vce只能放一个，并且使用残差分析的
中介

