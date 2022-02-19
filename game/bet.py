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
            
# after failing to create the game in play according to the Texas hold em rules I had to start over again. In the process of doing so, the fuction above became now useless.

                
