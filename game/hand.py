def makebest(line):
    shape=[]
    numbers=[]
    num_s.h=0#the number of shape heart
    num_s.d=0#the number of shape diamond
    num_s.s=0#the number of shape spade
    num_s.c=0#the number of shape clover
    num_n=0
    for i in range(len(line)):
        shape=shape+line[i][0]
        number=number+line[i][1]
    for i in range(len(shape)):
        if shape[i]=='H':
            num_s.h+=1
        if shape[i]=='D':
            num_s.d+=1
        if shape[i]=='S':
            num_s.s+=1
        if shape[i]=='C':
            num_s.c+=1
        

        

