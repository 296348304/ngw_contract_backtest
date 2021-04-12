__author__ = 'wangjian'


# 强平
def force_position(self, total_equity=None):
    total_equity_ = total_equity
    while True:
        if total_equity_ > 0:
            break
        # 随机平仓位
        positions = self.get_positions()
        pos_1 = list(positions.keys())[0]  # 'ag2101.SHFE'
        positipos_ins_1 = list(positions.values())[0]

        price = self.get_price(symbol_exchange=pos_1)
        lots = self.universe_lots.get(pos_1)
        amount = round(float(1 * price * lots), 4)

        if positipos_ins_1.get('long'):
            pre_volume = positipos_ins_1['long']['volume']
            now_volume = pre_volume - 1
            pre_avg_price = positipos_ins_1['long']['avg_price']
            pnl = (price - pre_avg_price) * 1

            if now_volume > 0:
                pre_margin = positipos_ins_1['long']['margin']
                avg_margin = pre_margin / pre_volume
                margin = round(avg_margin * 1, 4)
                now_margin = pre_margin - margin

                pnl = (price - pre_avg_price) * 1
                now_amount = positipos_ins_1['long']['amount'] - amount
                now_avg_price = round(float(now_amount / (now_volume * lots)), 4)

                # 最后在赋值
                self.get_positions()[pos_1]['long']['margin'] = now_margin
                self.get_positions()[pos_1]['long']['volume'] = now_volume
                self.get_positions()[pos_1]['long']['avg_price'] = now_avg_price
                self.get_positions()[pos_1]['long']['amount'] = now_amount
            else:
                # 平仓完 清0
                margin = positipos_ins_1['long']['margin']
                self.get_positions()[pos_1]['long'] = {}
            force_money = pnl + margin

        else:
            pre_volume = positipos_ins_1['short']['volume']
            now_volume = pre_volume - 1
            pre_avg_price = positipos_ins_1['short']['avg_price']
            pnl = (pre_avg_price - price) * 1

            if now_volume > 0:
                pre_margin = positipos_ins_1['short']['margin']
                avg_margin = pre_margin / pre_volume
                margin = round(avg_margin * 1, 4)
                now_margin = pre_margin - margin

                pnl = (price - pre_avg_price) * 1
                now_amount = positipos_ins_1['short']['amount'] - amount
                now_avg_price = round(float(now_amount / (now_volume * lots)), 4)

                # 最后在赋值
                self.get_positions()[pos_1]['short']['margin'] = now_margin
                self.get_positions()[pos_1]['short']['volume'] = now_volume
                self.get_positions()[pos_1]['short']['avg_price'] = now_avg_price
                self.get_positions()[pos_1]['short']['amount'] = now_amount
            else:
                # 平仓完 清0
                margin = positipos_ins_1['short']['margin']
                self.get_positions()[pos_1]['short'] = {}
            force_money = pnl + margin

        total_equity_ += force_money
    return round(total_equity_, 4)