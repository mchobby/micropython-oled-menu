from machine import SoftI2C, Pin
from oledmenu import *

# Oled display requires a SoftI2C to work properly
i2c = SoftI2C(sda=Pin(6), scl=Pin(7)) # I2C(1) : GP6=SDA, GP7=SCL

menu = OLED_MENU( i2c );

# Callback to draw screen/dashboard
#
start = None
def on_dash_start( ctrl ):
	# Start is used to initialize
	global start
	start = time.ticks_ms()

def on_dash_draw( ctrl, oled, enc ): # ScreenControler, Oled Screen, Encoder
	global start
	oled.fill( 0 )
	oled.text( "%i" % int(time.ticks_diff( time.ticks_ms(),start )) , 5, 20, 1 )
	oled.show() # update screen

# code, Label
menu.add_label( "start", "Start Oven" )
menu.add_range( "preheat" , "PreHeat %s C", 25, 180, 5, 50 ) # Min, Max, Step, default
menu.add_screen( "scr1", "Dashboard", on_dash_draw, on_dash_start ) # code, Label and optional "cargo object"


menu.start()

while True:
	if menu.update(): # true when entry selected
		entry = menu.selected # will reset selection
		if entry:
			print( "%s selected" % entry )

		if entry and entry.code=="scr1":
			print( "%s has been showed" % entry.code ) # the my_ref reference given in add_screen
	# Process other tasks here
