import start, opp
import sys 
sys.path.append("C:/Users/nkjan/Documents/GitHub/pokercommunity/game/play.py")
credit=1000
name=start.start()
status=True
while (status or credit>1000):
    play=opp.opp(credit)
    if play==True:
        print('Lets play')

if status==False:
    print('YOu won')
elif credit<1000:
    print("you lost")
