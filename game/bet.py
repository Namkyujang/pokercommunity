import random
def gamble(mybet,ophand,comcards,credit,pool,opponent):
    showdown=ophand+comcards
    point=0
    for i in range(len(showdown)):
        cmbn=[]
        if showdown[i][1]='1':
            cmbn.append(showdown[i])
            if len(cmbn)==2:
                point+=2
            if len(cmbn)==3:
                point+=5
            


                
