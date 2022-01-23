import start, opp
import game.play
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
