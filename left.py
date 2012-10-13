import time
import autopy as ap
from autopy.mouse import LEFT_BUTTON

def leftClick():
    ap.mouse.click(LEFT_BUTTON)
    time.sleep(.1)
    print "# click"
    
def leftDown():
    ap.mouse.toggle(True, LEFT_BUTTON)
    time.sleep(.1)
    print '# left down'

def leftUp():
    ap.mouse.toggle(False, LEFT_BUTTON)
    time.sleep(.1)
    print '# left release'
    
#############################################################################
    
if __name__ == "__main__":
    time.sleep(1)
    leftClick()
    leftDown()
    time.sleep(3)
    leftUp()