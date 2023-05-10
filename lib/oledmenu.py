
# OLED Display 128 x 64 pixels (ADF 938) @ 0x3d
# I2C Rotary Encoder (U135) @ 0x40

from icons8 import NO
from icontls import draw_icon
import time

# ------------------------------------------------------------------------------
#   MENU ITEM
# ------------------------------------------------------------------------------

class MenuItem:
	__slots__ = ( "owner","code","label", "enabled", "_focus", "cargo", "visible", "_selected", "_selected_until" )

	def __init__(self, owner, code, label, enabled ):
		self.owner = owner
		self.code  = code
		self.label = label
		self.enabled = enabled
		self._focus = False
		self.visible = True
		self._selected = False
		self._selected_ticks = None # _selected flag may vary so fast that user could not have the time to see it!
		                            # So we can decided to maintain the visiual effect for a minimum amount of time!
		self.cargo = None

	def __repr__(self):
		if (self.cargo != None) and ('value' in dir(self.cargo)):
			return '<%s "%s">' % (self.code, self.label % self.cargo.value )
		else:
			return '<%s "%s">' % (self.code, self.label)

	def draw( self, oled, x, y ):
		# Display menu entry from position x, y
		if not(self.visible):
			return
		# Draw the background (WHITE when selected otherwise BLACK)
		if self._selected or ( (self._selected_ticks!=None) and ( time.ticks_diff( time.ticks_ms(), self._selected_ticks) < 750 ) ):
			_bg = 1 # White
		else:
			_bg = 0 # black

		_fg = 1 if _bg==0 else 0
		oled.rect(x,y,self.owner.item_width,self.owner.item_height+2, _bg, _bg )
		# draw the content
		_x_off = 1
		if not(self.enabled):
			draw_icon( oled, NO, x+1, y+1, _fg  )
			_x_off = 11

		if (self.cargo != None) and ('value' in dir(self.cargo) ):
			oled.text( self.label % self.cargo.value , x+_x_off, y+2, _fg )
		else:
			oled.text( self.label, x+_x_off, y+2, _fg )
		if self._focus:
			oled.rect(x,y,self.owner.item_width,self.owner.item_height+2, _fg )

	@property
	def focus( self ):
		return self._focus

	@focus.setter
	def focus( self, value ):
		self._focus = value

	@property
	def selected( self ):
		return self._selected

	@selected.setter
	def selected( self, value ):
		self._selected = value
		if value:
			self._selected_ticks = time.ticks_ms()

# ------------------------------------------------------------------------------
#   MENU controler
# ------------------------------------------------------------------------------

class RangeControler:
	__slots__ = ( "owner", "parent", "min_val","max_val", "step", "default_val" )

	def __init__(self, owner, parent, min_val, max_val, step, default_value ):
		self.owner = owner # owner = Oled Menu
		self.parent = parent # Parent of controler = Menu item
		self.min_val = min_val
		self.max_val = max_val
		self.step = step
		self.value = default_value
		self.selected = False

	def inc( self ):
		self.value += self.step
		if self.value > self.max_val:
			self.value = self.max_val

	def dec( self ):
		self.value -= self.step
		if self.value < self.min_val:
			self.value = self.min_val

	def start( self ):
		self.owner.enc.reset()
		# wait for the button to be released
		while self.owner.enc.button:
			time.sleep_ms( 10 )
		self.selected = False # become True when user press the Encoder Button
		                      # once again when the configuration is done

	def draw( self, oled ):
		oled.fill( 0 )
		oled.text( self.parent.label % self.value, 0, 0, 1 )

		oled.show()


	def update( self ):
		# return True when the user press the button to confirm
		oled = self.owner.oled
		enc =  self.owner.enc

		# Return True if an entry is selected
		_pos = enc.rel_position;
		if _pos > 1:
			self.inc()
		elif _pos < -1:
			self.dec()
		enc.reset();

		self.draw( oled )

		if enc.button:
			self.selected = True

		return self.selected



class ScreenControler:
	""" Used to inform mainloop to draw its own screen/dashboard """
	__slots__ = ( "owner", "parent", "selected", "_on_start", "_on_draw" )

	def __init__(self, owner, parent, _on_screen_draw, _on_screen_start ):
		self.owner = owner # owner = Oled Menu
		self.parent = parent # Parent of controler = Menu item
		self._on_start = _on_screen_start # Callback to initiate screen drawing
		self._on_draw = _on_screen_draw # Callback to draw the screen
		self.selected = False

	def start( self ):
		self.owner.enc.reset()
		# wait for the button to be released
		while self.owner.enc.button:
			time.sleep_ms( 10 )
		self.selected = False # become True when user press the Encoder Button
		                      # once again when the configuration is done
		self.owner.oled.fill( 0 ) # clear the screen
		if self._on_start:
			self._on_start( self ) # Caller is the controler
		self.owner.oled.show()

	def update( self ):
		# return True when the user press the button to confirm
		#oled = self.owner.oled
		enc =  self.owner.enc
		if self._on_draw != None:
			self._on_draw( self, self.owner.oled, self.owner.enc )

		# If button is pressed Then we do quit the controler
		if enc.button:
			self.selected = True

		return self.selected


# ------------------------------------------------------------------------------
#   OLED MENU
# ------------------------------------------------------------------------------

class OLED_MENU:
	def __init__( self, i2c ):
		self.i2c = i2c
		self.items = [] # List of MenuItem
		self.item_height = 10; # including border
		self.item_width = None; # depend of OLED detected
		self._selected = None; # Menu entry that have been selected
		self._selected_time = time.time(); # When the entry has been selected

		# -- Demarrer l' OLED --
		from ssd1306 import SSD1306_I2C
		self.oled =  SSD1306_I2C( 128, 64, i2c, addr=0x3d )
		self.oled.fill(1) # Rempli l'écran en blanc
		self.oled.show()  # Afficher!
		self.item_width = self.oled.width-4 # There is a general X offset of 4 pixels

		# -- Démarrer l'encoder --
		from i2cenc import I2CRelEncoder
		self.enc = I2CRelEncoder(i2c)
		self._button_state = self.enc.button

	def add_label( self, code, label, enabled=True ):
		""" Add menu item """
		menu_item = MenuItem( self, code, label, enabled )
		self.items.append( menu_item )
		return menu_item

	def add_range( self, code, label, min_val, max_val, step, default_val, enabled=True ):
		""" Add 'Integer Controler' menu item """
		menu_item = self.add_label( code, label, enabled )
		menu_item.cargo = RangeControler( self, menu_item, min_val, max_val, step, default_val )

	def add_screen( self, code, label, on_draw, on_start=None, enabled=True ):
		""" Add 'User Screen Controler' menu item """
		menu_item = self.add_label( code, label, enabled )
		menu_item.cargo = ScreenControler( self, menu_item, on_draw, on_start ) # Owner, Parent, Callback called when screen must be drawed


	def start( self ):
		# Initialize the structure
		self.top_index = self.first_visible_from( 0 ) # Index of the first entry to display on the screen
		self.set_focus( self.top_index )
		self.enc.reset()

	def by_code( self, code ):
		""" retreive a menu entry by its code """
		for item in self.items:
			if item.code == code:
				return item
		return None
	#-----------------------------------------
	#   Utilities
	#
	@property
	def selected( self ):
		""" Return ref to selected MenuItem. Selection is clear as soon as read """
		_idx = self._selected
		# Clear selection as soon as it is read by callee!
		if self._selected!=None:
			if self.items[_idx].cargo==None:
				self.set_selected(None)
			else:
				# transfet the control to the controler (until it finished)
				if self.items[_idx].cargo.selected:
					self.set_selected(None)
				else:
					return None # don't say that menu is selected as long as the
		# return reference to the selected item (if any)
		if _idx!=None:
			return self.items[_idx]

		return None

	def first_visible_from( self, _from_index ):
		for i in range( len(self.items) ):
			if (i >= _from_index) and self.items[i].visible:
				return i
		return len(self.items)

	def set_focus( self, index ): # Activate the focus for a given index
		for i in range(len(self.items)):
			(self.items[i]).focus = (i==index)
		# Is the focus in the visible area (vertical menu)
		_x_top = index*self.item_height
		_x_bottom = _x_top +  self.item_height
		# auto-scroll down
		if _x_bottom > (self.top_index*self.item_height)+self.oled.height:
			self.top_index = index-(self.oled.height//self.item_height)+1
		elif _x_top < (self.top_index*self.item_height):
			self.top_index = index

	def get_focus_index( self ):
		for i in range( len(self.items) ):
			if self.items[i].focus:
				return i
		return None

	def focus_next( self ):
		_curr = self.get_focus_index()
		if _curr==None:
			return
		_curr += 1
		while _curr < len(self.items):
			if self.items[_curr].visible and self.items[_curr].enabled:
				self.set_focus(_curr)
				return
			_curr += 1

	def focus_prev( self ):
		_curr = self.get_focus_index()
		if _curr==None:
			return
		_curr -= 1
		while _curr >= 0:
			if self.items[_curr].visible and self.items[_curr].enabled:
				self.set_focus(_curr)
				return
			_curr -= 1

	def set_selected( self, index ):
		self._selected = index
		for i in range(len(self.items)):
			self.items[i].selected = (i==index)


	def draw( self ):
		# Update the display
		self.oled.fill(0) # black
		# _max = self.oled_height // self.item_height
		_index = self.top_index
		_x = 4
		_y = 0
		while (_index<len(self.items)) and (_y < self.oled.height):
			if not( self.items[_index].visible ):
				_index += 1
				continue
			self.items[_index].draw( self.oled, _x, _y )
			_y += self.item_height
			_index += 1
		self.oled.show()


	def update( self ):
		# Is the selected item have a dedocated controler ????
		if self._selected and self.items[self._selected].cargo:
			return self.items[self._selected].cargo.update()
		# Call it as often as possible
		# Return True if an entry is selected
		_pos = self.enc.rel_position
		# reset selected state after 5 second
		if (self._selected!=None) and (time.time() - self._selected_time )>5 :
			self.set_selected( None )

		# What to focus
		if abs(_pos) > 3:
			if _pos > 0:
				self.focus_next()
			else:
				self.focus_prev()
			self.enc.reset()

		# Detect button pressure with a state machine (avoids multiple triggers)
		_state = self.enc.button
		if _state != self._button_state: # If button state changed
			if not(self._button_state) and _state: # released button
				self.set_selected( self.get_focus_index() )
				self._selected_time = time.time()
		self._button_state = _state

		# Refresh the menu on screen
		self.draw()
		# Start the cargo (if it applies)
		if self._selected != None:
			if self.items[ self._selected ].cargo != None:
				self.items[ self._selected ].cargo.start() # Prepare controller to be displayed

		return self._selected != None
