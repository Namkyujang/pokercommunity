import random
def game1(credit):
    s=['Sa','S2','S3','S4','S5','S6','S7','S8','S9','S10','SK','SQ','SJ']
    d=['Da','D2','D3','D4','D5','D6','D7','D8','D9','D10','DK','DQ','DJ']
    h=['Ha','H2','H3','H4','H5','H6','H7','H8','H9','H10','HK','HQ','HJ']
    c=['Ca','C2','C3','C4','C5','C6','C7','C8','C9','C10','CK','CQ','CJ']
    pool=0
    pack=s+d+h+c
    random.shuffle(pack)
    opphand=pack[2]
    myhand=pack[2:4]
    coke==True
    while coke==True:
        mybet=int(input('How much you gonna bet:'))
        if mybet<credit:
            credit=credit-mybet
            hisbet=mybet*2
            pool=mybet+hisbet
            coke==False
        else:
            print('Too much')
    print(pool)
    print(pack[4:7])
    while pick==True:
        