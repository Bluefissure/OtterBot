info = '''白萝卜价格趋势模型(简体中文)
Github: InsulatingShell
https://github.com/InsulatingShell/ACTurnipPriceModel-cn/
微博：@绝缘壳
版本：v 1.1.1
最后更新时间： Mar 25
修复了 无法判断今天是否是三期型/四期型售价峰值 的问题
'''


class Turnip(object):

    def __init__(self, price_list=None):
        self.price_list = [] if not price_list else price_list
        self.inc = 0 #记录是否上涨
        self.dec = 0 #记录连续下跌次数
        self.fir = 0
        self.sec = 0
        self.thr = 0
        self.fou = 0
        self.flag_fluc = False
        self.flag_decr = False
        self.flag_3 = False
        self.flag_4 = False
        self.lock_fluc = False
        #期望
        self.expe_fluc = 0
        self.expe_3 = 0
        self.expe_4 = 0
        self.now = -1
        self.last = -1
        self.lock_3 = False
        self.lock_4 = False

    def get_price(self, day, am_pm="am"):
        if day == 0:
            return self.price_list[0]
        idx = day * 2 - (1 if am_pm == "am" else 0)
        return self.price_list[idx]

    def make_prediction(self):
        msg = ""
        if self.lock_fluc:
            self.flag_fluc = True
            self.flag_decr = False
            self.flag_3 = False
            self.flag_4 = False
        if self.inc == 0 and self.dec >=8 :
            self.flag_decr = True
            self.flag_3 = False
            self.flag_4 = False
        if self.flag_fluc == True:
            self.expe_fluc = int(1.1*self.get_price(0))
            if self.flag_decr or self.flag_3 or self.flag_4:
                msg += "目前可能是波动型，"
            else:
                msg += "目前是波动型，"
            msg += "则最大卖价范围在{}至{}之间。".format(self.expe_fluc, int(1.45 * self.get_price(0)))
            if float(1.45*self.get_price(0)) > float(self.today) >= float(self.expe_fluc):
                msg += "今日售价已有可能是波动型价格的最大值，可以考虑今天卖出。"
            if float(1.45*self.get_price(0)) <= float(self.today):
                msg += "今日售价就是波动型价格的最大值，建议今天卖出。"
            else:
                msg += "\n"
        if self.flag_3:
            self.expe_3 = int(2 * self.get_price(0))
            if self.flag_decr or self.flag_fluc or self.flag_4:
                msg += "目前可能是三期型，"
            else:
                self.lock_3 = True
                msg += "目前就是三期型，"
            msg += "则最大卖价范围在{}至{}之间".format(self.expe_3, int(6 * self.get_price(0)))
            if self.thr != 0:
                if self.lock_3:
                    msg += "今天就是三期型的售价峰值，请卖出。"
                else:
                    msg += "今天可能是三期型的售价峰值，可以考虑卖出。"
        if self.flag_4 == True:
            self.expe_4 = int(1.4 * self.get_price(0))
            if self.flag_decr or self.flag_fluc or self.flag_3:
                msg += "目前可能是四期型，"
            else:
                self.lock_4 = True
                msg += "目前就是四期型，"
            msg += "则最大卖价范围在{}至{}之间。".format(self.expe_4, int(2 * self.get_price(0)))
            if self.fou != 0:
                if self.lock_4:
                    msg += "今天就是四期型的售价峰值，请卖出。"
                else:
                    msg += "今天可能是四期型的售价峰值，可以考虑卖出。"
        if self.flag_decr == True:
            if self.flag_4 or self.flag_fluc or self.flag_3:
                msg += "目前可能是递减型，要做好可能会亏的准备"
            else:
                msg += "目前就是递减型，只会越来越便宜，建议现在卖了或者等待朋友开门。"
        return msg

    def rough_model(self):
        assert self.get_price(0) > 0, "需要周日买入的菜价数据"
        assert self.get_price(1, "am") > 0, "需要周一上午的菜价数据"
        X = (self.get_price(1, "am") / self.get_price(0)) * 100
        if  91 <= X <= 100:
            #print('可能是"波动型"或"4期型"')
            self.flag_fluc = True
            self.flag_4 = True
        elif 85 <= X < 91:
            #print('可能是"3期型"或"4期型"或"递减型"')
            self.flag_3 = True
            self.flag_4 = True
            self.flag_decr = True
        elif 80 <= X < 85:
            #print('可能是"3期型"或"4期型"')
            self.flag_3 = True
            self.flag_4 = True
        elif 60 <= X < 80:
            #print('可能是"波动型"或"4期型"')
            self.flag_fluc = True
            self.flag_4 = True
        elif X < 60:
            # print('接近"四期型"')
            self.flag_4 = True
        elif X > 100:
            #print('波动型，有这么好的事？最高售价预计',int(1.1*float(self.sun)),'至',int(1.45*float(self.sun)))
            self.flag_fluc = True
            self.lock_fluc = True
        return ""

    def record_price(self):
        if self.lock_fluc == False:
            if self.flag_3 or self.flag_4:
                if self.inc == 1:
                    self.fir = self.now
                elif self.inc >= 1:
                    if self.fir != 0 and self.sec == 0:
                        self.sec = self.now
                    elif self.fir != 0 and self.sec != 0 and self.thr == 0:
                        self.thr = self.now
                    elif self.flag_4 and self.flag_3 == False and self.fir != 0 and self.sec != 0 and self.thr != 0 and self.fou ==0 :
                        self.fou = self.now
        return ""

    def compare_last_price(self):
        if (float(self.last) >= float(self.now)):
            if self.inc == 0: #连续下跌
                self.dec = self.dec + 1
            #else:
                #self.inc = self.inc + 1
        else:
            #print("if (",float(self.last)," <= ",float(self.now),",:")
            self.inc = self.inc + 1
        if self.dec == 8: #周四下午都没变调
            return "周四下午都没发生变调吗？情况不妙，趁早离手。\n"
            self.flag_4 = False
            self.flag_3 = False
        return ""
        #print("inc = ", self.inc)
        #print("dec = ",self.dec)

    def load_price_list(self, price_list=None):
        if price_list:
            self.price_list = price_list
        i2s = lambda x: str(x) if x > 0 else "-"
        price_msg = ""
        for i, price in enumerate(self.price_list):
            price_msg += i2s(price) if i == 0 else (
                ("/"+i2s(price)) if i % 2 == 0 else (" "+i2s(price))
            )
        final_msg = ""
        for i, price in enumerate(self.price_list):
            if i == 0:
                self.today = self.get_price(0)
            elif i == 1:
                self.last = self.now
                self.now = self.get_price(1, "am")
                self.rough_model()
                msg = self.make_prediction()
                if(float(self.get_price(1, "am")) <= float(self.get_price(0))):
                    self.dec = self.dec + 1
                else:
                    self.lock_fluc = True
                if msg.strip():
                    final_msg = msg.strip()
            else:
                day = (i + 1) // 2
                am_pm = "am" if i % 2 == 1 else "pm"
                self.last = self.now
                self.now = self.get_price(day, am_pm)
                msg = self.compare_last_price()
                self.record_price()
                msg += self.make_prediction()
                if day == 6 and am_pm == "pm":
                    msg += "\n周六下午了害搁这等呢，赶快卖了吧。"
                if msg.strip():
                    final_msg = msg.strip()
        return "{}:\n{}".format(price_msg, final_msg)

    # DRY

    # def Sun(self):
    #     print('请输入周日买入价，回车结束输入')
    #     sun_raw = readInput()
    #     self.sun = SunPriceCheck(sun_raw)
    #     print('周日买入价为：', self.sun)
    #     self.today = self.sun
    #     print('')

    # def Mon_AM(self):
    #     self.last = self.now
    #     print('请输入周一上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.mon_am = priceCheck(raw_input) #
    #     print('周一上午收购价为：', self.mon_am) #
    #     self.now = self.mon_am #
    #     self.rough_model(self)
    #     self.make_prediction(self)
    #     if(float(self.mon_am) <= float(self.sun)):
    #         self.dec = self.dec+1
    #     else:
    #         self.lock_fluc = True
    #     print('')

    # def Mon_PM(self):
    #     self.last = self.now
    #     print('请输入周一下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.mon_pm = priceCheck(raw_input)  #
    #     print('周一下午收购价为：', self.mon_pm)  #
    #     self.now = self.mon_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Tue_AM(self):
    #     self.last = self.now
    #     print('请输入周二上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.tue_am = priceCheck(raw_input)  #
    #     print('周二上午收购价为：', self.tue_am)  #
    #     self.now = self.tue_am  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Tue_PM(self):
    #     self.last = self.now
    #     print('请输入周二下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.tue_pm = priceCheck(raw_input)  #
    #     print('周二下午收购价为：', self.tue_pm)  #
    #     self.now = self.tue_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Wed_AM(self):
    #     self.last = self.now
    #     print('请输入周三上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.wed_am = priceCheck(raw_input)  #
    #     print('周三上午收购价为：', self.wed_am)  #
    #     self.now = self.wed_am  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Wed_PM(self):
    #     self.last = self.now
    #     print('请输入周三下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.wed_pm = priceCheck(raw_input)  #
    #     print('周三下午收购价为：', self.wed_pm)  #
    #     self.now = self.wed_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Thu_AM(self):
    #     self.last = self.now
    #     print('请输入周四上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.thu_am = priceCheck(raw_input)  #
    #     print('周四上午收购价为：', self.thu_am)  #
    #     self.now = self.thu_am  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Thu_PM(self):
    #     self.last = self.now
    #     print('请输入周四下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.thu_pm = priceCheck(raw_input)  #
    #     print('周四下午收购价为：', self.thu_pm)  #
    #     self.now = self.thu_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Fri_AM(self):
    #     self.last = self.now
    #     print('请输入周五上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.fri_am = priceCheck(raw_input)  #
    #     print('周五上午收购价为：', self.fri_am)  #
    #     self.now = self.fri_am  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Fri_PM(self):
    #     self.last = self.now
    #     print('请输入周五下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.fri_pm = priceCheck(raw_input)  #
    #     print('周五下午收购价为：', self.fri_pm)  #
    #     self.now = self.fri_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Sat_AM(self):
    #     self.last = self.now
    #     print('请输入周六上午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.sat_am = priceCheck(raw_input)  #
    #     print('周六上午收购价为：', self.sat_am)  #
    #     self.now = self.sat_am  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('')

    # def Sat_PM(self):
    #     self.last = self.now
    #     print('请输入周六下午收购价，回车结束输入')
    #     raw_input = readInput()
    #     self.sat_pm = priceCheck(raw_input)  #
    #     print('周六下午收购价为：', self.sat_pm)  #
    #     self.now = self.sat_pm  #
    #     self.compare_last_price(self)
    #     self.record_price(self)
    #     self.make_prediction(self)
    #     print('不过现在都周六下午了，无论如何都请卖了，否则全烂了')
    #     print('')