#!/usr/bin/env python3
"""
Download Mao Zedong Selected Works (Volumes 1-5) from marxists.org,
convert to UTF-8 Markdown, and organize by volume.
"""

import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Output base directory
OUTPUT_BASE = Path("/home/jaimeparker/Projects/stable-jarvis/mao-selected-works")

# Base URL for articles
BASE_URL = "https://www.marxists.org/chinese/maozedong/"

# Article definitions: (title, filename_suffix, volume)
# Volume 1: 第一次国内革命战争时期 + 第二次国内革命战争时期
VOLUME_1 = [
    ("中国社会各阶级的分析", "marxist.org-chinese-mao-19251201.htm"),
    ("湖南农民运动考察报告", "marxist.org-chinese-mao-192703.htm"),
    ("中国的红色政权为什么能够存在？", "marxist.org-chinese-mao-19281005.htm"),
    ("井冈山的斗争", "marxist.org-chinese-mao-19281125.htm"),
    ("关于纠正党内的错误思想", "marxist.org-chinese-mao-192912.htm"),
    ("星星之火，可以燎原", "marxist.org-chinese-mao-19300105.htm"),
    ("反对本本主义", "marxist.org-chinese-mao-193005.htm"),
    ("必须注意经济工作", "marxist.org-chinese-mao-19330812.htm"),
    ("怎样分析农村阶级", "marxist.org-chinese-mao-193310.htm"),
    ("我们的经济政策", "marxist.org-chinese-mao-193401.htm"),
    ("关心群众生活，注意工作方法", "marxist.org-chinese-mao-19340127.htm"),
    ("论反对日本帝国主义的策略", "marxist.org-chinese-mao-19351227.htm"),
    ("中国革命战争的战略问题", "marxist.org-chinese-mao-193612.htm"),
    ("关于蒋介石声明的声明", "marxist.org-chinese-mao-19361228.htm"),
    ("中国共产党在抗日时期的任务", "marxist.org-chinese-mao-19370503.htm"),
    ("为争取千百万群众进入抗日民族统一战线而斗争", "marxist.org-chinese-mao-19370508.htm"),
    ("实践论", "marxist.org-chinese-mao-193707.htm"),
    ("矛盾论", "marxist.org-chinese-mao-193708.htm"),
]

# Volume 2: 抗日战争时期（上）
VOLUME_2 = [
    ("反对日本进攻的方针、办法和前途", "marxist.org-chinese-mao-19370723.htm"),
    ("为动员一切力量争取抗战胜利而斗争", "marxist.org-chinese-mao-19370825.htm"),
    ("反对自由主义", "marxist.org-chinese-mao-19370907.htm"),
    ("国共合作成立后的迫切任务", "marxist.org-chinese-mao-19370929.htm"),
    ("和英国记者贝特兰的谈话", "marxist.org-chinese-mao-19371025.htm"),
    ("上海太原失陷以后抗日战争的形势和任务", "marxist.org-chinese-mao-19371112.htm"),
    ("陕甘宁边区政府第八路军后方留守处布告", "marxist.org-chinese-mao-19380515.htm"),
    ("抗日游击战争的战略问题", "marxist.org-chinese-mao-193805.htm"),
    ("论持久战", "marxist.org-chinese-mao-193805b.htm"),
    ("中国共产党在民族战争中的地位", "marxist.org-chinese-mao-19381014.htm"),
    ("统一战线中的独立自主问题", "marxist.org-chinese-mao-19381105.htm"),
    ("战争和战略问题", "marxist.org-chinese-mao-19381106.htm"),
    ("五四运动", "marxist.org-chinese-mao-19390501.htm"),
    ("青年运动的方向", "marxist.org-chinese-mao-19390504.htm"),
    ("反对投降活动", "marxist.org-chinese-mao-19390630.htm"),
    ("必须制裁反动派", "marxist.org-chinese-mao-19390801.htm"),
    ("关于国际新形势对新华日报记者的谈话", "marxist.org-chinese-mao-19390901.htm"),
    ("和中央社、扫荡报、新民报三记者的谈话", "marxist.org-chinese-mao-19390916.htm"),
    ("苏联利益和人类利益的一致", "marxist.org-chinese-mao-19390928.htm"),
    ("《共产党人》发刊词", "marxist.org-chinese-mao-19391004.htm"),
    ("目前形势和党的任务", "marxist.org-chinese-mao-19391010.htm"),
    ("大量吸收知识分子", "marxist.org-chinese-mao-19391201.htm"),
    ("中国革命和中国共产党", "marxist.org-chinese-mao-193912.htm"),
    ("斯大林是中国人民的朋友", "marxist.org-chinese-mao-19391220.htm"),
    ("纪念白求恩", "marxist.org-chinese-mao-19391221.htm"),
    ("新民主主义论", "marxist.org-chinese-mao-194001.htm"),
    ("克服投降危险，力争时局好转", "marxist.org-chinese-mao-19400128.htm"),
    ("团结一切抗日力量，反对反共顽固派", "marxist.org-chinese-mao-19400201.htm"),
    ("向国民党的十点要求", "marxist.org-chinese-mao-19400201b.htm"),
    ("《中国工人》发刊词", "marxist.org-chinese-mao-19400207.htm"),
    ("必须强调团结和进步", "marxist.org-chinese-mao-19400207b.htm"),
    ("新民主主义的宪政", "marxist.org-chinese-mao-19400220.htm"),
    ("抗日根据地的政权问题", "marxist.org-chinese-mao-19400306.htm"),
    ("目前抗日统一战线中的策略问题", "marxist.org-chinese-mao-19400311.htm"),
    ("放手发展抗日力量，抵抗反共顽固派的进攻", "marxist.org-chinese-mao-19400504.htm"),
    ("团结到底", "marxist.org-chinese-mao-19400705.htm"),
    ("论政策", "marxist.org-chinese-mao-19401225.htm"),
    ("为皖南事变发表的命令和谈话", "marxist.org-chinese-mao-19410120.htm"),
    ("打退第二次反共高潮后的时局", "marxist.org-chinese-mao-19410318.htm"),
    ("关于打退第二次反共高潮的总结", "marxist.org-chinese-mao-19410508.htm"),
]

# Volume 3: 抗日战争时期（下）
VOLUME_3 = [
    ("《农村调查》的序言和跋", "marxist.org-chinese-mao-194134.htm"),
    ("改造我们的学习", "marxist.org-chinese-mao-19410519.htm"),
    ("揭破远东慕尼黑的阴谋", "marxist.org-chinese-mao-19410525.htm"),
    ("关于反法西斯的国际统一战线", "marxist.org-chinese-mao-19410623.htm"),
    ("在陕甘宁边区参议会的演说", "marxist.org-chinese-mao-19411106.htm"),
    ("整顿党的作风", "marxist.org-chinese-mao-19420201.htm"),
    ("反对党八股", "marxist.org-chinese-mao-19420208.htm"),
    ("在延安文艺座谈会上的讲话", "marxist.org-chinese-mao-194205.htm"),
    ("一个极其重要的政策", "marxist.org-chinese-mao-19420907.htm"),
    ("第二次世界大战的转折点", "marxist.org-chinese-mao-19421012.htm"),
    ("祝十月革命二十五周年", "marxist.org-chinese-mao-19421106.htm"),
    ("抗日时期的经济问题和财政问题", "marxist.org-chinese-mao-194212.htm"),
    ("关于领导方法的若干问题", "marxist.org-chinese-mao-19430601.htm"),
    ("质问国民党", "marxist.org-chinese-mao-19430712.htm"),
    ("开展根据地的减租、生产和拥政爱民运动", "marxist.org-chinese-mao-19431001.htm"),
    ("评国民党十一中全会和三届二次国民参政会", "marxist.org-chinese-mao-19431005.htm"),
    ("组织起来", "marxist.org-chinese-mao-19431129.htm"),
    ("学习和时局", "marxist.org-chinese-mao-19440412.htm"),
    ("为人民服务", "marxist.org-chinese-mao-19440908.htm"),
    ("评蒋介石在双十节的演说", "marxist.org-chinese-mao-19441011.htm"),
    ("文化工作中的统一战线", "marxist.org-chinese-mao-19441030.htm"),
    ("必须学会做经济工作", "marxist.org-chinese-mao-19450110.htm"),
    ("游击区也能够进行生产", "marxist.org-chinese-mao-19450131.htm"),
    ("两个中国之命运", "marxist.org-chinese-mao-19450423.htm"),
    ("论联合政府", "marxist.org-chinese-mao-19450424.htm"),
    ("愚公移山", "marxist.org-chinese-mao-19450611.htm"),
    ("论军队生产自给，兼论整风和生产两大运动的重要性", "marxist.org-chinese-mao-19450427.htm"),
    ("赫尔利和蒋介石的双簧已经破产", "marxist.org-chinese-mao-19450710.htm"),
    ("评赫尔利政策的危险", "marxist.org-chinese-mao-19450712.htm"),
    ("给福斯特同志的电报", "marxist.org-chinese-mao-19450729.htm"),
    ("对日寇的最后一战", "marxist.org-chinese-mao-19450809.htm"),
]

# Volume 4: 第三次国内革命战争时期
VOLUME_4 = [
    ("抗日战争胜利后的时局和我们的方针", "marxist.org-chinese-mao-19450813.htm"),
    ("蒋介石在挑动内战", "marxist.org-chinese-mao-19450813b.htm"),
    ("第十八集团军总司令给蒋介石的两个电报", "marxist.org-chinese-mao-194508.htm"),
    ("评蒋介石发言人谈话", "marxist.org-chinese-mao-19450816.htm"),
    ("中共中央关于同国民党进行和平谈判的通知", "marxist.org-chinese-mao-19450826.htm"),
    ("关于重庆谈判", "marxist.org-chinese-mao-19451017.htm"),
    ("国民党进攻的真相", "marxist.org-chinese-mao-19451105.htm"),
    ("减租和生产是保卫解放区的两件大事", "marxist.org-chinese-mao-19451107.htm"),
    ("一九四六年解放区工作的方针", "marxist.org-chinese-mao-19451215.htm"),
    ("建立巩固的东北根据地", "marxist.org-chinese-mao-19451228.htm"),
    ("关于目前国际形势的几点估计", "marxist.org-chinese-mao-194604.htm"),
    ("以自卫战争粉碎蒋介石的进攻", "marxist.org-chinese-mao-19460720.htm"),
    ("和美国记者安娜·路易斯·斯特朗的谈话", "marxist.org-chinese-mao-19460806.htm"),
    ("集中优势兵力，各个歼灭敌人", "marxist.org-chinese-mao-19460916.htm"),
    ("美国「调解」真相和中国内战前途", "marxist.org-chinese-mao-19460929.htm"),
    ("三个月总结", "marxist.org-chinese-mao-19461001.htm"),
    ("迎接中国革命的新高潮", "marxist.org-chinese-mao-19470201.htm"),
    ("中共中央关于暂时放弃延安和保卫陕甘宁边区的两个文件", "marxist.org-chinese-mao-194611and194704.htm"),
    ("关于西北战场的作战方针", "marxist.org-chinese-mao-19470415.htm"),
    ("蒋介石政府已处在全民的包围中", "marxist.org-chinese-mao-19470530.htm"),
    ("解放战争第二年的战略方针", "marxist.org-chinese-mao-19470901.htm"),
    ("中国人民解放军宣言", "marxist.org-chinese-mao-19471010.htm"),
    ("中国人民解放军总部关于重行颁布三大纪律八项注意的训令", "marxist.org-chinese-mao-19471010a.htm"),
    ("目前形势和我们的任务", "marxist.org-chinese-mao-19471225.htm"),
    ("关于建立报告制度", "marxist.org-chinese-mao-19480107.htm"),
    ("关于目前党的政策中的几个重要问题", "marxist.org-chinese-mao-19480118.htm"),
    ("军队内部的民主运动", "marxist.org-chinese-mao-19480130.htm"),
    ("在不同地区实施土地法的不同策略", "marxist.org-chinese-mao-19480203.htm"),
    ("纠正土地改革宣传中的「左」倾错误", "marxist.org-chinese-mao-19480211.htm"),
    ("新解放区土地改革要点", "marxist.org-chinese-mao-19480215.htm"),
    ("关于工商业政策", "marxist.org-chinese-mao-19480227.htm"),
    ("关于民族资产阶级和开明绅士问题", "marxist.org-chinese-mao-19480301.htm"),
    ("评西北大捷兼论解放军的新式整军运动", "marxist.org-chinese-mao-19480307.htm"),
    ("关于情况的通报", "marxist.org-chinese-mao-19480320.htm"),
    ("在晋绥干部会议上的讲话", "marxist.org-chinese-mao-19480401.htm"),
    ("对晋绥日报编辑人员的谈话", "marxist.org-chinese-mao-19480402.htm"),
    ("再克洛阳后给洛阳前线指挥部的电报", "marxist.org-chinese-mao-19480408.htm"),
    ("新解放区农村工作的策略问题", "marxist.org-chinese-mao-19480524.htm"),
    ("一九四八年的土地改革工作和整党工作", "marxist.org-chinese-mao-19480525.htm"),
    ("关于辽沈战役的作战方针", "marxist.org-chinese-mao-194809and10.htm"),
    ("关于健全党委制", "marxist.org-chinese-mao-19480920.htm"),
    ("中共中央关于九月会议的通知", "marxist.org-chinese-mao-19481001.htm"),
    ("关于淮海战役的作战方针", "marxist.org-chinese-mao-19481011.htm"),
    ("全世界革命力量团结起来，反对帝国主义的侵略", "marxist.org-chinese-mao-194811.htm"),
    ("中国军事形势的重大变化", "marxist.org-chinese-mao-19481114.htm"),
    ("关于平津战役的作战方针", "marxist.org-chinese-mao-19481211.htm"),
    ("敦促杜聿明等投降书", "marxist.org-chinese-mao-19481217.htm"),
    ("将革命进行到底", "marxist.org-chinese-mao-19481230.htm"),
    ("评战犯求和", "marxist.org-chinese-mao-19490104.htm"),
    ("中共中央毛泽东主席关于时局的声明", "marxist.org-chinese-mao-19490114.htm"),
    ("中共发言人评南京行政院的决议", "marxist.org-chinese-mao-19490121.htm"),
    ("中共发言人关于命令国民党反动政府重新逮捕前日本侵华军总司令冈村宁次和逮捕国民党内战罪犯的谈话", "marxist.org-chinese-mao-19490128.htm"),
    ("中共发言人关于和平条件必须包括惩办日本战犯和国民党战犯的声明", "marxist.org-chinese-mao-19490205.htm"),
    ("把军队变为工作队", "marxist.org-chinese-mao-19490208a.htm"),
    ("四分五裂的反动派为什么还要空喊「全面和平」？", "marxist.org-chinese-mao-19490215.htm"),
    ("国民党反动派由「呼吁和平」变为呼吁战争", "marxist.org-chinese-mao-19490216.htm"),
    ("评国民党对战争责任问题的几种答案", "marxist.org-chinese-mao-19490218.htm"),
    ("在中国共产党第七届中央委员会第二次全体会议上的报告", "marxist.org-chinese-mao-19490305.htm"),
    ("党委会的工作方法", "marxist.org-chinese-mao-19490313.htm"),
    ("南京政府向何处去？", "marxist.org-chinese-mao-19490404.htm"),
    ("向全国进军的命令", "marxist.org-chinese-mao-19490421.htm"),
    ("中国人民解放军布告", "marxist.org-chinese-mao-19490425.htm"),
    ("中国人民解放军总部发言人为英国军舰暴行发表的声明", "marxist.org-chinese-mao-19490330.htm"),
    ("在新政治协商会议筹备会上的讲话", "marxist.org-chinese-mao-19490615.htm"),
    ("论人民民主专政", "marxist.org-chinese-mao-19490630.htm"),
    ("丢掉幻想，准备斗争", "marxist.org-chinese-mao-19490814.htm"),
    ("别了，司徒雷登", "marxist.org-chinese-mao-19490818.htm"),
    ("为什么要讨论白皮书？", "marxist.org-chinese-mao-19490828.htm"),
    ("「友谊」，还是侵略？", "marxist.org-chinese-mao-19490830.htm"),
    ("唯心历史观的破产", "marxist.org-chinese-mao-19490916.htm"),
]

# Volume 5: 社会主义革命和社会主义建设时期（一）
VOLUME_5 = [
    ("出版说明", "marxist.org-chinese-mao-vol5.htm"),
    ("中国人民站起来了", "marxist.org-chinese-mao-19490921.htm"),
    ("中国人民大团结万岁", "marxist.org-chinese-mao-19490930.htm"),
    ("人民英雄们永垂不朽", "marxist.org-chinese-mao-19490930b.htm"),
    ("永远保持艰苦奋斗的作风", "marxist.org-chinese-mao-19491026.htm"),
    ("征询对待富农策略问题的意见", "marxist.org-chinese-mao-19500312.htm"),
    ("为争取国家财政经济状况的基本好转而斗争", "marxist.org-chinese-mao-19500606.htm"),
    ("不要四面出击", "marxist.org-chinese-mao-19500606b.htm"),
    ("做一个完全的革命派", "marxist.org-chinese-mao-19500623.htm"),
    ("你们是全民族的模范人物", "marxist.org-chinese-mao-19500925.htm"),
    ("给中国人民志愿军的命令", "marxist.org-chinese-mao-19501008.htm"),
    ("中国人民志愿军要爱护朝鲜的一山一水一草一木", "marxist.org-chinese-mao-19510119.htm"),
    ("中共中央政治局扩大会议决议要点", "marxist.org-chinese-mao-19510218.htm"),
    ("镇压反革命必须实行党的群众路线", "marxist.org-chinese-mao-19510515.htm"),
    ("镇压反革命必须打得稳，打得准，打得狠", "marxist.org-chinese-mao-195012.htm"),
    ("应当重视电影《武训传》的讨论", "marxist.org-chinese-mao-19510520.htm"),
    ("三大运动的伟大胜利", "marxist.org-chinese-mao-19511023.htm"),
    ("关于「三反」、「五反」的斗争", "marxist.org-chinese-mao-195111.htm"),
    ("把农业互助合作当作一件大事去做", "marxist.org-chinese-mao-19511215.htm"),
    ("元旦祝词", "marxist.org-chinese-mao-19520101.htm"),
    ("中共中央关于西藏工作方针的指示", "marxist.org-chinese-mao-19520406.htm"),
    ("工人阶级与资产阶级的矛盾是国内的主要矛盾", "marxist.org-chinese-mao-19520606.htm"),
    ("团结起来，划清敌我界限", "marxist.org-chinese-mao-19520804.htm"),
    ("祝贺中国人民志愿军的重大胜利", "marxist.org-chinese-mao-19521024.htm"),
    ("反对官僚主义、命令主义和违法乱纪", "marxist.org-chinese-mao-19530105.htm"),
    ("批判大汉族主义", "marxist.org-chinese-mao-19530316.htm"),
    ("解决「五多」问题", "marxist.org-chinese-mao-19530319.htm"),
    ("对刘少奇、杨尚昆破坏纪律擅自以中央名义发出文件的批评", "marxist.org-chinese-mao-19530519.htm"),
    ("批判离开总路线的右倾观点", "marxist.org-chinese-mao-19530615.htm"),
    ("青年团的工作要照顾青年的特点", "marxist.org-chinese-mao-19530630.htm"),
    ("关于国家资本主义", "marxist.org-chinese-mao-19530709.htm"),
    ("党在过渡时期的总路线", "marxist.org-chinese-mao-195308.htm"),
    ("反对党内的资产阶级思想", "marxist.org-chinese-mao-19530812.htm"),
    ("改造资本主义工商业的必经之路", "marxist.org-chinese-mao-19530907.htm"),
    ("抗美援朝的伟大胜利和今后的任务", "marxist.org-chinese-mao-19530912.htm"),
    ("批判梁漱溟的反动思想", "marxist.org-chinese-mao-19530916.htm"),
    ("关于农业互助合作的两次谈话", "marxist.org-chinese-mao-19531015.htm"),
    ("关于中华人民共和国宪法草案", "marxist.org-chinese-mao-19540614.htm"),
    ("为建设一个伟大的社会主义国家而奋斗", "marxist.org-chinese-mao-19540915.htm"),
    ("关于《红楼梦》研究问题的信", "marxist.org-chinese-mao-19541016.htm"),
    ("原子弹吓不倒中国人民", "marxist.org-chinese-mao-19550128.htm"),
    ("在中国共产党全国代表会议上的讲话", "marxist.org-chinese-mao-195503.htm"),
    ("驳「舆论一律」", "marxist.org-chinese-mao-19550524.htm"),
    ("《关于胡风反革命集团的材料》的序言和按语", "marxist.org-chinese-mao-195505.htm"),
    ("关于农业合作化问题", "marxist.org-chinese-mao-19550731.htm"),
    ("农业合作化必须依靠党团员和贫农下中农", "marxist.org-chinese-mao-19550907.htm"),
    ("农业合作化的一场辩论和当前的阶级斗争", "marxist.org-chinese-mao-19551011.htm"),
    ("《中国农村的社会主义高潮》的序言", "marxist.org-chinese-mao-195509.htm"),
    ("《中国农村的社会主义高潮》的按语", "marxist.org-chinese-mao-195509a.htm"),
    ("征询对农业十七条的意见", "marxist.org-chinese-mao-19551221.htm"),
    ("加快手工业的社会主义改造", "marxist.org-chinese-mao-19560304.htm"),
    ("论十大关系", "marxist.org-chinese-mao-19560425.htm"),
    ("美帝国主义是纸老虎", "marxist.org-chinese-mao-19560714.htm"),
    ("增强党的团结，继承党的传统", "marxist.org-chinese-mao-19560830.htm"),
    ("我们党的一些历史经验", "marxist.org-chinese-mao-195600925.htm"),
    ("纪念孙中山先生", "marxist.org-chinese-mao-19561112.htm"),
    ("在中国共产党第八届中央委员会第二次全体会议上的讲话", "marxist.org-chinese-mao-19561115.htm"),
    ("在省市自治区党委书记会议上的讲话", "marxist.org-chinese-mao-195701.htm"),
    ("关于正确处理人民内部矛盾的问题", "marxist.org-chinese-mao-19570227.htm"),
    ("在中国共产党全国宣传工作会议上的讲话", "marxist.org-chinese-mao-19570312.htm"),
    ("坚持艰苦奋斗，密切联系群众", "marxist.org-chinese-mao-195703.htm"),
    ("事情正在起变化", "marxist.org-chinese-mao-19570515.htm"),
    ("中国共产党是全中国人民的领导核心", "marxist.org-chinese-mao-19570525.htm"),
    ("组织力量反击右派分子的猖狂进攻", "marxist.org-chinese-mao-19570608.htm"),
    ("文汇报的资产阶级方向应当批判", "marxist.org-chinese-mao-19570701.htm"),
    ("打退资产阶级右派的进攻", "marxist.org-chinese-mao-19570709.htm"),
    ("一九五七年夏季的形势", "marxist.org-chinese-mao-195707.htm"),
    ("做革命的促进派", "marxist.org-chinese-mao-19571009.htm"),
    ("坚定地相信群众的大多数", "marxist.org-chinese-mao-19571013.htm"),
    ("党内团结的辩证方法", "marxist.org-chinese-mao-19571118.htm"),
    ("一切反动派都是纸老虎", "marxist.org-chinese-mao-19571118a.htm"),
]

VOLUMES = [
    (1, "第一次国内革命战争时期·第二次国内革命战争时期", VOLUME_1),
    (2, "抗日战争时期（上）", VOLUME_2),
    (3, "抗日战争时期（下）", VOLUME_3),
    (4, "第三次国内革命战争时期", VOLUME_4),
    (5, "社会主义革命和社会主义建设时期（一）", VOLUME_5),
]


def sanitize_filename(name):
    """Remove characters unsafe for filenames."""
    unsafe = '<>:"/\\|?*'
    for c in unsafe:
        name = name.replace(c, "")
    return name.strip()


def download_and_convert(title, filename, vol_num, article_index):
    """Download a single article, convert to markdown."""
    url = BASE_URL + filename
    temp_html = f"/tmp/mao-article-{vol_num}-{article_index}.html"
    temp_utf8 = f"/tmp/mao-article-{vol_num}-{article_index}-utf8.html"

    try:
        # Download with User-Agent header
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()

        # Save raw bytes
        with open(temp_html, "wb") as f:
            f.write(raw)

        # Convert encoding from GB2312/GBK to UTF-8
        decoded = None
        for encoding in ["gb2312", "gbk", "gb18030", "utf-8"]:
            try:
                decoded = raw.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if decoded is None:
            print(f"  ERROR: Cannot decode {title}")
            return False

        # Write UTF-8 version
        with open(temp_utf8, "w", encoding="utf-8") as f:
            f.write(decoded)

        # Use markitdown for conversion
        result = subprocess.run(
            ["markitdown", temp_utf8],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"  ERROR: markitdown failed for {title}: {result.stderr[:200]}")
            return False

        markdown = result.stdout

        # Add YAML frontmatter with metadata
        safe_title = title.replace('"', '「').replace("'", "'")
        header = f"""---
title: "{safe_title}"
volume: {vol_num}
source: "{url}"
---

"""
        markdown = header + markdown

        # Create output filename
        safe_fname = sanitize_filename(title)
        fname = f"{article_index:03d}-{safe_fname}.md"
        out_dir = OUTPUT_BASE / f"vol-{vol_num:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / fname

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"  OK: {title} ({len(markdown)} chars)")
        return True

    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {title}: {url}")
        return False
    except Exception as e:
        print(f"  EXCEPTION: {e} for {title}")
        return False
    finally:
        # Cleanup temp files
        for tf in [temp_html, temp_utf8]:
            if os.path.exists(tf):
                os.remove(tf)


def main():
    total = sum(len(v[2]) for v in VOLUMES)
    print(f"Downloading {total} articles across {len(VOLUMES)} volumes...")
    print(f"Output directory: {OUTPUT_BASE}")
    print()

    success = 0
    fail = 0

    for vol_num, vol_name, articles in VOLUMES:
        print(f"{'='*60}")
        print(f"Volume {vol_num}: {vol_name} ({len(articles)} articles)")
        print(f"{'='*60}")

        for i, (title, filename) in enumerate(articles, 1):
            print(f"[{success+fail+1}/{total}] Vol{vol_num}-{i:03d}: {title}")
            if download_and_convert(title, filename, vol_num, i):
                success += 1
            else:
                fail += 1
            # Be polite to the server
            time.sleep(0.5)

        print()

    # Create README
    readme_path = OUTPUT_BASE / "README.md"
    readme_content = f"""# 毛泽东选集 (Mao Zedong Selected Works)

来源: [中文马克思主义文库](https://www.marxists.org/chinese/maozedong/index.htm)
下载时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
总计: {total} 篇文章

## 各卷目录

"""
    for vol_num, vol_name, articles in VOLUMES:
        readme_content += f"\n### 第{vol_num}卷：{vol_name}\n\n"
        for i, (title, _) in enumerate(articles, 1):
            readme_content += f"{i}. [{title}](vol-{vol_num:02d}/{i:03d}-{sanitize_filename(title)}.md)\n"

    readme_content += f"""
## 统计

- 成功: {success}
- 失败: {fail}
- 总计: {total}
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} succeeded, {fail} failed out of {total}")
    print(f"Output: {OUTPUT_BASE}")


if __name__ == "__main__":
    main()
