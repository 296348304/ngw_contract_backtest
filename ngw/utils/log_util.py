# 日志输出到文件
import logging
import os
logger = logging.getLogger()
dirs = '/home/admin/logs/ngw_contract_backtest/'
if not os.path.exists(dirs):
    os.makedirs(dirs)

# a 追加   w 覆盖
logging.basicConfig(
    level=logging.INFO,
    filename='/home/admin/logs/ngw_contract_backtest/ngw_contract_backtest.log',
    filemode='a+',
    format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s:%(message)s")


def print(message1=None, message2=None, message3=None, message4=None, message5=None, message6=None, message7=None,
          message8=None, message9=None, message10=None, message11=None, message12=None, message13=None, message14=None,
          flush=None, end=None,sep=None):
    str_all = ''
    ms_list = [message1,message2,message3,message4,message5,message6,
               message7,message8,message9,message10,message11,message12,
               message13,message14]
    for i in ms_list:
        if isinstance(i,pd.DataFrame):
            str1 = str(i)
        else:
            str1 = str(i) if i else ''
        str_all += str1
    logger.info(str_all)


