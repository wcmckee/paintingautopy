import autopy as ap
from autopy.mouse import LEFT_BUTTON
import time
import random




def rect_move():
    
    start = random.randint(300, 600)
    mid = random.randint(600, 900)
    bottom = random.randint(900, 1200)

    ap.mouse.move(start, 800)
    ap.mouse.click(LEFT_BUTTON)
    time.sleep(.1)
    print "# click"
    ap.mouse.toggle(True, LEFT_BUTTON)
    time.sleep(.1)
    print '# left down'
    ap.mouse.smooth_move(mid, bottom)
    ap.mouse.smooth_move(start, bottom)
    ap.mouse.smooth_move(bottom, mid)
    ap.mouse.smooth_move(start, mid)
    ap.mouse.toggle(False, LEFT_BUTTON)
    time.sleep(.1)
    print '# left release'

def test2():
    ap.mouse.move(500,300)
    ap.mouse.click(LEFT_BUTTON)
    time.sleep(.1)
    print "# click"
    ap.mouse.toggle(True, LEFT_BUTTON)
    time.sleep(.1)
    print '# left down'
    ap.mouse.smooth_move(800,300)
    ap.mouse.smooth_move(800, 900)
    ap.mouse.smooth_move(500, 900)
    ap.mouse.smooth_move(500,300)
    ap.mouse.toggle(False, LEFT_BUTTON)
    time.sleep(.1)
    print '# left release'

    
def screen_option():
    ap.screen.get_size()
    print ap.screen.get_size()
    
screen_option
                
                  
##  move_forward
         
##  for x in range(0, 3):
  ##rect_move()

