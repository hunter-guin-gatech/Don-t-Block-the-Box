#! /usr/bin/python
# -*- coding: utf-8 -*-

#
# tkinter example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""
A simple example for VLC python bindings using tkinter. Uses python 2.7

Base code reference#
Author: Patrick Fay
Date: 23-09-2015
"""

# import external libraries
import vlc 
#import libvlc
import sys
import csv
import numpy
import datetime
import Tix as tk
from Tkinter import *
from PIL import ImageTk, Image, ImageOps
##import ImageTk
##import Image

if sys.version_info[0] < 3:
    import Tkinter as Tk
    # from Tkinter import ttk
    import ttk
    # from Tkinter.filedialog import askopenfilename
    # import askopenfilename
    import tkFileDialog
else:
    import tkinter as Tk
    # from Tkinter import ttk
    import ttk
    # from Tkinter.filedialog import askopenfilename
    # import askopenfilename
    import tkFileDialog

# import standard libraries
import os
import pathlib
from threading import Timer,Thread,Event
import time
import platform

class ttkTimer(Thread):
    """a class serving same function as wxTimer... but there may be better ways to do this
    """
    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

running1 = True
running2 = True

class Player(Tk.Frame):
    """The main window has to deal with events.
    """
    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)
    
        self.parent = parent
        
        if title == None:
            title = "Video 1"
        self.parent.title(title)

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        ww = ws/2 # width for the Tk root
        hh = hs/2 # height for the Tk root

        # calculate x and y coordinates for the Tk root window
        x = 0
        y = 0

        # set the dimensions of the screen 
        # and where it is placed
        parent.geometry('%dx%d+%d+%d' % (ww, hh, x, y))

        global w1
        w1 = StringVar()
        w1.set('Video1')

        global timelabel1
        timelabel1 = StringVar()
        #timelabel1.set("00:00:00")
        
        global customskip1
        customskip1 = IntVar()

        # Menu Bar
        #   File Menu
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        fileMenu = Tk.Menu(menubar)

        fileMenu.add_command(label="Open 1", command = lambda win = self: OnOpen(win))
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)        

        self.parent.bind_all("<space>",OnPause3)
            
        # The second panel holds controls
        self.player = None

        self.videopanel1 = ttk.Frame(self.parent)
        self.videopanel2 = ttk.Frame(self.parent)

        self.canvas1 = Tk.Canvas(self.videopanel1).pack(fill=Tk.BOTH,expand=1)
        self.videopanel1.pack(fill=Tk.BOTH,expand=1)
        
        ## Controls for player 1
        ctrlpanel = Tk.Frame(self.parent)
        self.timelabeltext = '00:00:00'
        self.tlabel = Tk.Label(ctrlpanel, text=self.timelabeltext)
        play   = Tk.Button(ctrlpanel, text="Play", command = lambda win = self:OnPlay(win))
        pause  = Tk.Button(ctrlpanel, text="Pause", command = lambda win = self:OnPause(win))
       
        fast   = Tk.Button(ctrlpanel, text="Play (2x)", command = lambda win = self:OnFastPlay(win))
        slow   = Tk.Button(ctrlpanel, text="Play (0.5x)", command = lambda win = self:OnSlowPlay(win))
        backskip = Tk.Button(ctrlpanel, width = 12,text="Backward skip(s)", command = lambda win = self:backskip1(win))
        label = Tk.Label(ctrlpanel, text="Custom Skip (s)")
        self.entry = Entry(ctrlpanel)
        forskip = Tk.Button(ctrlpanel, width = 12, text="Forward skip(s)", command = lambda win = self:forskip1(win))
        
        self.tlabel.pack(side=Tk.LEFT)
        slow.pack(side=Tk.LEFT)
        play.pack(side=Tk.LEFT)
##        stop.pack(side=Tk.LEFT)
        fast.pack(side=Tk.LEFT)
        pause.pack(side=Tk.LEFT)
        backskip.pack(side=Tk.LEFT)
        label.pack(side=Tk.LEFT)
        self.entry.pack(side=Tk.LEFT)
        forskip.pack(side=Tk.LEFT)
##        panel.pack(side=Tk.RIGHT)
        ctrlpanel.pack(side=Tk.BOTTOM)

        ## timeslider for player 1
        ctrlpanel2 = Tk.Frame(self.parent)
        self.scale_var1 = Tk.DoubleVar()
        self.timeslider_last_val1 = ""

        self.timeslider1 = Tk.Scale(ctrlpanel2, variable=self.scale_var1, command = self.scale_sel, 
                from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider1.pack(side=Tk.BOTTOM, fill=Tk.X,expand=1)
        self.timeslider_last_update1 = time.time()
        ctrlpanel2.pack(side=Tk.BOTTOM,fill=Tk.X)
        
        # Timer updation
        self.timer1 = ttkTimer(self.OnTimer, 1.0)
        self.timer1.start()
        self.parent.update()
        self.update_clock()
        

    def OnTimer(self):
        """Update the time slider according to the current movie time.
        """
        if self.player1 == None:
            return
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length1 = self.player1.get_length()
        
##        print"length1"
##        print length1
        
        dbl = length1 * 0.001
        self.timeslider1.config(to=dbl)

        # update the time on the slider
        tyme1 = self.player1.get_time()
        
        if tyme1 == -1:
            tyme1 = 0
        dbl = tyme1 * 0.001
        self.timeslider_last_val1 = ("%.0f" % dbl) + ".0"
        # don't want to programatically change slider while user is messing with it.
        # wait 2 seconds after user lets go of slider
        if time.time() > (self.timeslider_last_update1 + 2.0):
            self.timeslider1.set(dbl)

    def update_clock(self):
        tymelabel1 =self.player1.get_time()
        timelabel1.set(msToHMS(tymelabel1))
        self.timelabeltext = str(timelabel1.get())
        self.tlabel.config(text=self.timelabeltext)
        self.parent.after(1000,self.update_clock)


    def scale_sel(self, evt):
        if self.player1 == None:
            return
        nval1 = self.scale_var1.get()

##        print"nval1"
##        print nval1
        
        sval1 = str(nval1)
        if self.timeslider_last_val1 != sval1:
            self.timeslider_last_update1 = time.time()
            mval1 = "%.0f" % (nval1 * 1000)
            self.player1.set_time(int(mval1)) # expects milliseconds


    def GetHandle(self):
        return self.videopanel1.winfo_id()

        
    def OnPlay(self):
        """Toggle the status to Play/Pause.
        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not self.player1.get_media():
            self.OnOpen()
        else:
            # Try to launch the media, if this fails display an error message
            if self.player1.play() == -1:
                self.errorDialog("Unable to play.")

    def OnStop(self):
        """Stop the player.
        """
        self.player1.stop()
        # reset the time slider
        self.timeslider1.set(0)

Player.Instance1 = vlc.Instance()
Player.player1 = Player.Instance1.media_player_new()


class Player2(Tk.Frame):
    """The main window has to deal with events.
    """
    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)
    
        self.parent = parent
        
        if title == None:
            title = "Video 2"

        self.parent.title(title)

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        ww = (ws/2) # width for the Tk root
        hh = (hs/2) # height for the Tk root

        # calculate x and y coordinates for the Tk root window
        x = ww
        y = 0

        # set the dimensions of the screen 
        # and where it is placed
        parent.geometry('%dx%d+%d+%d' % (ww, hh, x, y))
        
        global w2
        w2 = StringVar()
        w2.set('Video2')

        global customskip2
        customskip2 = IntVar()

        global timelabel2
        timelabel2 = StringVar()
        
        # Menu Bar
        #   File Menu
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        fileMenu = Tk.Menu(menubar)
        fileMenu.add_command(label="Open 2", command = lambda win = self: OnOpen2(win))
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)        

        self.parent.bind_all("<space>",OnPause3)

        #if running2 == False:
        #self.parent.bind("<space>",lambda win = self:OnPlay2(win,event = "<space>"))
            
        # The second panel holds controls
        self.player = None
        self.videopanel2 = ttk.Frame(self.parent)
        
        ## Player 2 canvas
        self.canvas2 = Tk.Canvas(self.videopanel2).pack(side=Tk.LEFT,fill=Tk.BOTH,expand=1)
        self.videopanel2.pack(fill=Tk.BOTH,expand=1)

        ## Player 2 controls
        ctrlpanel3 = Tk.Frame(self.parent)
        pause2  = Tk.Button(ctrlpanel3, text="Pause", command = lambda win = self:OnPause2(win))
        play2 = Tk.Button(ctrlpanel3, text="Play", command = lambda win = self:OnPlay2(win))
        fast2   = Tk.Button(ctrlpanel3, text="Play (2x)", command = lambda win = self:OnFastPlay2(win))
        slow2   = Tk.Button(ctrlpanel3, text="Play (0.5x)", command = lambda win = self:OnSlowPlay2(win))
##        stop2   = ttk.Button(ctrlpanel3, text="Stop", command = lambda win = self:OnStop2(win))
        backskip = Tk.Button(ctrlpanel3, width = 12,text="Backward skip(s)", command = lambda win = self:backskip2(win))
        label = Tk.Label(ctrlpanel3, text="Custom Skip (s)")
        self.entry = Entry(ctrlpanel3)
        forskip = Tk.Button(ctrlpanel3, width = 12, text="Forward skip(s)", command = lambda win = self:forskip2(win))
        self.timelabeltext2 = '00:00:00'
        self.tlabel2 = Tk.Label(ctrlpanel3, text=self.timelabeltext2)

        self.tlabel2.pack(side=Tk.LEFT)
        slow2.pack(side=Tk.LEFT)
        play2.pack(side=Tk.LEFT)
        fast2.pack(side=Tk.LEFT)
        pause2.pack(side=Tk.LEFT)
        backskip.pack(side=Tk.LEFT)
        label.pack(side=Tk.LEFT)
        self.entry.pack(side=Tk.LEFT)
        forskip.pack(side=Tk.LEFT)
##        stop2.pack(side=Tk.LEFT)
        ctrlpanel3.pack(side=Tk.BOTTOM)
        
        ## Player 2 timeslider
        ctrlpanel4 = ttk.Frame(self.parent)
        self.scale_var2 = Tk.DoubleVar()
        self.timeslider_last_val2 = ""
        self.timeslider2 = Tk.Scale(ctrlpanel4, variable=self.scale_var2, command = self.scale_sel2, 
                from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider2.pack(side=Tk.BOTTOM, fill=Tk.X,expand=1)
        self.timeslider_last_update2 = time.time()
        ctrlpanel4.pack(side=Tk.BOTTOM,fill=Tk.X)

        # Timer updation
        self.timer2 = ttkTimer(self.OnTimer2, 1.0)
        self.timer2.start()
        self.parent.update()
        self.update_clock2()

    def OnTimer2(self):
        """Update the time slider according to the current movie time.
        """
        if self.player2 == None:
            return
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length2 = self.player2.get_length()
        db2 = length2 * 0.001
        self.timeslider2.config(to=db2)

        # update the time on the slider
        tyme2 = self.player2.get_time()
        
        if tyme2 == -1:
            tyme2 = 0
        db2 = tyme2 * 0.001
        self.timeslider_last_val2 = ("%.0f" % db2) + ".0"
        # don't want to programatically change slider while user is messing with it.
        # wait 2 seconds after user lets go of slider
        if time.time() > (self.timeslider_last_update2 + 2.0):
            self.timeslider2.set(db2)

    def update_clock2(self):
        tymelabel2 =self.player2.get_time()
        timelabel2.set(msToHMS(tymelabel2))
        self.timelabeltext2 = str(timelabel2.get())
        self.tlabel2.config(text=self.timelabeltext2)
        self.parent.after(1000,self.update_clock2)

    def scale_sel2(self, evt):
        if self.player2 == None:
            return
        nval2 = self.scale_var2.get()
        sval2 = str(nval2)
        if self.timeslider_last_val2 != sval2:
            self.timeslider_last_update2 = time.time()
            mval2 = "%.0f" % (nval2 * 1000)
            self.player2.set_time(int(mval2)) # expects milliseconds

    def GetHandle2(self):
        return self.videopanel2.winfo_id()

    def OnStop2(self):
        """Stop the player.
        """
        self.player2.stop()
        # reset the time slider
        self.timeslider2.set(0)

    def OnPlay2(self):
        """Toggle the status to Play/Pause.
        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not self.player2.get_media():
            self.OnOpen2()
        else:
            # Try to launch the media, if this fails display an error message
            #win.player2.pause()
            self.player2.set_rate(1)
            #print win.player2.get_rate()
            global running2
            running2 = True
            if self.player2.play() == -1:
                self.errorDialog("Unable to play.")    

Player2.Instance2 = vlc.Instance()
Player2.player2 = Player2.Instance2.media_player_new()


global click
click = 0

def combine_funcs(*funcs):
    def combined_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)
    return combined_func

k =[[],[],[],[]]
l =[[],[],[],[]]
# create a dictionary of key:value pairs
dict = {}
global w
global h
w = 10
h = 1
alpha = ["", 'Time - Video 1', 'Time - Video 2', 'Vehicle Type', 'Comments', '', 'Time - Video 1 (2)', 'Time - Video 2 (2)','Vehicle Type (2)','Comments (2)','J','','']  
beta = ["Custom Skip","URA","Intersection Name","Lane #"]
gamma = [['Time - Video 1', 'Time - Video 2', 'Vehicle Type', 'Comments']] 

class Controls(Tk.Frame):
    """The main window has to deal with events.
    """
    
    def __init__(self, parent, title=None):

        Tk.Frame.__init__(self, parent)
        global vehicleid
        vehicleid = StringVar()
        global timestamp1
        timestamp1 = StringVar()
        global timestamp2
        timestamp2 = StringVar()
        global dtime
        dtime = StringVar()
        global customskip
        customskip = IntVar()
        global uraname
        uraname = StringVar()
        uraname.set('URA Name')
        global intersectionname
        intersectionname = StringVar()
        intersectionname.set('Intersection Name')
        global lanenumber
        lanenumber = StringVar()
        lanenumber.set('LaneNumber')
        global counter
        counter = IntVar()
        counter.set(0)
        global counter2
        counter2 = IntVar()
        counter2.set(0)
        
        
        self.grid()
        self.parent = parent

        if title == None:
            title = "Controls: Propensity Extraction"

        self.parent.title(title)

                # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        ww = ws/1.2 # width for the Tk root
        hh = (hs/2) # height for the Tk root

        # calculate x and y coordinates for the Tk root window
        x = ws/7
        y = (hs/2)+60

        # set the dimensions of the screen 
        # and where it is placed
        parent.geometry('%dx%d+%d+%d' % (ww, hh, x, y))

        self.canvas1 = Tk.Canvas(parent, width= 30, height = 30, borderwidth=0)
        self.canvas2 = Tk.Canvas(parent, borderwidth=0)
        self.frame1 = Tk.Frame(self.canvas1)
        self.frame2 = Tk.Frame(self.canvas2)

        self.vsb = Tk.Scrollbar(parent, orient="vertical", command=self.canvas2.yview)
        self.canvas2.configure(yscrollcommand=self.vsb.set)
        self.hsb = Tk.Scrollbar(parent, orient="horizontal", command=self.canvas2.xview)
        self.canvas2.configure(xscrollcommand=self.hsb.set)
        
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill ="x")
        self.canvas1.pack(side="top", fill="both", expand=True)
        self.canvas2.pack(side="bottom", fill="both", expand=True)
        self.canvas1.create_window((4,3), window=self.frame1, anchor="nw", tags="self.frame1")
        self.canvas2.create_window((4,3), window=self.frame2, anchor="nw", tags="self.frame2")
		
        self.frame2.bind("<Configure>", self.onFrameConfigure)
        self.populate()
        self.frame1.bind_all("<space>",OnPause3)
        self.frame2.bind_all("<space>",OnPause3)
        self.frame1.bind("<space>",OnPause3)
        self.frame2.bind("<space>",OnPause3)
        self.canvas2.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas2.yview_scroll(-1*(event.delta/120), "units")

    def populate(self):
        def click(event, cell):
        # can do different things with right (3) and left (1) mouse button clicks
            self.parent.title("you clicked mouse button %d in cell %s" % (event.num, cell))
            
            # test right mouse button for equation solving
            # eg. data = '=9-3' would give 6
            if event.num == 3:
                if cell.startswith('Time - Video 1'):
                    # entry object in use
                    obj = dict[cell]
                    # get data in obj
                    data = obj.get()
                    obj.delete(0, 'end')
                    obj.insert(0, str(timestamp1.get()))

                if cell.startswith('Time - Video 2'):
                    # entry object in use
                    obj = dict[cell]
                    # get data in obj
                    data = obj.get()
                    obj.delete(0, 'end')
                    obj.insert(0, str(timestamp2.get()))
                else:
                    pass

        
        def writeToFile():
            p = [[],[],[],[]]
            q =[[],[],[],[]]
            r =[[],[],[]]
            for self.entry in k[0]:
                p[0].append(self.entry.get())
            for self.entry in l[0]:
                q[0].append(self.entry.get())
            for self.entry in k[1]:
                p[1].append(self.entry.get())
            for self.entry in l[1]:
                q[1].append(self.entry.get())
            for self.entry in k[2]:
                p[2].append(self.entry.get())
            for self.entry in l[2]:
                q[2].append(self.entry.get())
            for self.entry in k[3]:
                p[3].append(self.entry.get())
            for self.entry in l[3]:
                q[3].append(self.entry.get())
                
            s = numpy.column_stack((p[0],p[1],p[2],p[3]))
            t = numpy.column_stack((q[0],q[1],q[2],q[3]))
            u = numpy.concatenate((s,t))
            v = numpy.concatenate((gamma,u))
            #print v

            timestr = time.strftime("%Y%m%d-%H%M%S")


            if len(dict['URA'+str(4)].get()) != 0:
                uraname.set(str(dict['URA'+str(4)].get()))

            if len(dict['Intersection Name'+str(4)].get()) != 0:
                intersectionname.set(str(dict['Intersection Name'+str(4)].get()))

            if len(dict['Lane #'+str(6)].get()) != 0:
                lanenumber.set(str(dict['Lane #'+str(6)].get()))
                    
            csvname = 'P_'+str(intersectionname.get())+'_'+str(w1.get())+'_'+str(w2.get())+'_'+str(lanenumber.get())+'_'+timestr+'_'+str(uraname.get())+'.csv'
            #print csvname
                
            with open(csvname, "w") as csvfile:
                writer = csv.writer(csvfile, lineterminator='\n')
                for lists in v:
                    writer.writerow(lists)
                
                
        def key_r(event, cell):
            # return/enter has been pressed
            data = dict[cell].get()  # get text/data in given cell
            #print cell, dict[cell], data  # test
            self.parent.title("Cell %s contains %s" % (cell, data))

##        img = Image.open("gt.multi.jpg")
##        img = img.resize((250,40),Image.ANTIALIAS)
##        photoimg=ImageTk.PhotoImage(img)
##        panel = Label(self.frame,image=photoimg)
##        panel.image=photoimg
##        panel.grid(row =0, column =0)
        
        # Create button labels: row 0
        Label(self.frame1, width = 15, text="Synch Video Controls",fg="blue2").grid(row=0,column=2, sticky = E+W)
        Label(self.frame1, text="Custom Skip(s)",fg="blue2").grid(row=0,column=5,sticky = E+W)
        Label(self.frame1, width = 10, text="Vehicle Timestamp",fg="blue2").grid(row=0,column=8,sticky = E+W)
        Label(self.frame1, width = 10, text="Vehicle Type", fg="blue2").grid(row=0,column=11,sticky = E+W)
        Label(self.frame2, width = 5, text="URA", fg="blue").grid(row=3,column=12,sticky = E+W)
        Label(self.frame2, width = 15, text="Intersection Name", fg="blue").grid(row=3,column=13,sticky = E+W)
        Label(self.frame2, width = 5, text="Lane #", fg="blue").grid(row=5,column=12,sticky = E+W)
            
        # Create buttons: row 1
        Button(self.frame1,width = 12, text="Play(0.5X)", command = OnSlowPlay3).grid(row=1, column=0,sticky=E+W)
        Button(self.frame1,width = 12, text="Play/Pause", command = OnPause3).grid(row=1, column=1,sticky=E+W)
        Button(self.frame1, width = 12,text="Play(1X)", command = OnPlay3).grid(row=1, column=2,sticky=E+W)
        Button(self.frame1, width = 12,text="Play(2X)", command = OnFastPlay3).grid(row=1, column=3,sticky=E+W)
        #Button(parent, text="Stop", command = OnStop3).grid(row=0, column=3,sticky=E+W)
        Button(self.frame1, width = 12,text="Backward Skip(s)", command = lambda win = self:backskip(win)).grid(row=1, column=4, sticky=E+W) 
        Button(self.frame1, width = 12, text="Forward Skip(s)", command = lambda win = self:forskip(win)).grid(row=1, column=6, sticky=E+W) 
##        Button(self.frame, width = 12, text="Time - Video 1", command = lambda win = self:timestamp_vid1(win)).grid(row=1, column=6, sticky=E+W)
##        Button(self.frame, width = 12, text="Time - Video 2", command = lambda win = self:timestamp_vid2(win)).grid(row=1, column=7, sticky=E+W)
        Button(self.frame1, width = 12, text="Get Timestamps", command = lambda win = self:combine_funcs(timestamp_vid1(win),timestamp_vid2(win))).grid(row=1, column=8, sticky=E+W)
        Button(self.frame1, width = 12, text="Blocking", command=blocking).grid(row= 1, column = 10, sticky = E+W)
        Button(self.frame1, width = 12, text='Non Blocking', command=nonblocking).grid(row= 1, column = 11, sticky = E+W)
        Button(self.frame1, width = 12, text='None', command=none).grid(row= 1, column = 12, sticky = E+W)
        Button(self.frame1, width = 8,text='Load CSV', bg ="light blue",command=writeCSVtoTkinter).grid(row= 1, column = 14, sticky = E+W)
        Button(self.frame1, width = 8,text='Save To CSV', bg ="medium sea green",command=writeToFile).grid(row= 1, column = 15, sticky = E+W)

        for r in range(28):
            self.parent.rowconfigure(r, weight=1)    
        for c in range(12):
            self.parent.columnconfigure(c, weight=1)
            
        for r in range (1,7):
            for c in range (4,14):
                if r == 1 and c==5:
                    self.entry = Entry(self.frame1)
                    self.entry.grid(row=r, column=c, sticky = E+W)
                    cell = "%s%s" % (beta[c-5], r)
                    dict[cell] = self.entry
                           
                if r == 4 and c == 12:
                    self.entry = Entry(self.frame2, width = 5)
                    self.entry.grid(row=r, column=c, sticky = E+W)
                    cell = "%s%s" % (beta[c-11], r)
                    dict[cell] = self.entry
                           
                if r == 4 and c == 13:
                    self.entry = Entry(self.frame2, width = 8)
                    self.entry.grid(row=r, column=c, sticky = E+W)
                    cell = "%s%s" % (beta[c-11], r)
                    dict[cell] = self.entry

                if r == 6 and c == 12:
                    self.entry = Entry(self.frame2, width = 8)
                    self.entry.grid(row=r, column=c, sticky = E+W)
                    cell = "%s%s" % (beta[c-9], r)
                    dict[cell] = self.entry
            
        # create row labels
        for r in range(2,29):
            for c in range(10):

                if r == 2:
                    # create column labels
                    self.label1 = Label(self.frame2, width=15, text=alpha[c])
                    self.label1.grid(row=r, column=c, padx = 2, pady=2)
                        
                elif c == 0:
                    # create row labels
                    self.label1 = Label(self.frame2, width=3, text=str(r-2))
                    self.label1.grid(row=r, column=c, padx = 2, pady=2)

                elif c == 5:
                    # create row labels
                    self.label1 = Label(self.frame2, width=3, text=str(r+24))
                    self.label1.grid(row=r, column=c, padx = 2, pady=2)
                        
                else:
                    # create entry object
                    v = StringVar()
                    v.set('None')
                    self.entry1 = Entry(self.frame2, width=10)
                    # place the object
                    self.entry1.grid(row=r, column=c)

                    if c==1:
                        k[0].append(self.entry1)
                    if c==2:
                        k[1].append(self.entry1)
                    if c==3:
                        k[2].append(self.entry1)
                    if c==4:
                        k[3].append(self.entry1)
                    if c==6:
                        l[0].append(self.entry1)
                    if c==7:
                        l[1].append(self.entry1)
                    if c==8:
                        l[2].append(self.entry1)
                    if c==9:
                        l[3].append(self.entry1)
                        
                    # create a dictionary of cell:object pair
                    cell = "%s%s" % (alpha[c], r)
                    dict[cell] = self.entry1
     
                    if running1 == True and running2 == True:
                        self.entry1.bind("<space>",OnPause3)    
                    # bind the object to a left mouse click
                    self.entry1.bind('<Button-1>', lambda e, cell=cell: click(e, cell))
                    # bind the object to a right mouse click
                    self.entry1.bind('<Button-3>', lambda e, cell=cell: click(e, cell))
                    # bind the object to a return/enter press
                    self.entry1.bind('<Return>', lambda e, cell=cell: key_r(e, cell))


    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas2.configure(scrollregion=self.canvas2.bbox("all"))
               
def writeCSVtoTkinter():
    name = tkFileDialog.askopenfilename()
    #print name
    csv = numpy.genfromtxt(name,delimiter=",",dtype = None,skip_header=1)
    #print csv
    i=0
    for lists in csv:
        j = 0
        for number in lists:
            j+=1
            
            if j==3:
                i+=1
            #print i

            if i <26:
                if str(number).startswith('F'):
                    pass
                elif str(number)=='-1':
                    pass
                else:
                    dict[alpha[j]+str(i+3)].insert(0,str(number))
            else:
                if str(number).startswith('F'):
                    pass
                elif str(number)=='-1':
                    pass
                else:
                    dict[alpha[j+5]+str(i-23)].insert(0,str(number))

def msToHMS(f):
    ms = f%1000
    f = (f-ms)/1000
    secs = f%60
    f=(f-secs)/60
    mins=f%60
    hrs=(f-mins)/60
    return '%0*d'%(2,hrs)+":"+'%0*d'%(2,mins)+":"+'%0*d'%(2,secs)
    

def timestamp_vid1(win):
    timestamp_1 = Player.player1.get_time()
    timestamp1.set(msToHMS(timestamp_1))
    #print str(timestamp1.get())
    counter.set(counter.get()+1)
    #print counter.get()
    
    for r in range (3,29):
        if len(dict['Time - Video 1'+'28'].get()) == 0:
            if len(dict['Time - Video 1'+str(r)].get()) == 0:
                dict['Time - Video 1'+str(r)].insert(0,str(timestamp1.get()))
                break
            else:
                continue
        else:
            if len(dict['Time - Video 1 (2)'+str(r)].get()) == 0:
                dict['Time - Video 1 (2)'+str(r)].insert(0,str(timestamp1.get()))
                break
            else:
                continue

    if (counter.get()== 10 or counter.get() ==20 or counter.get() ==30 or counter.get() ==40 or counter.get()==50):
        p1 = [[],[],[],[]]
        q1 =[[],[],[],[]]
        for Controls.entry in k[0]:
            p1[0].append(Controls.entry.get())
        for Controls.entry in l[0]:
            q1[0].append(Controls.entry.get())
        for Controls.entry in k[1]:
            p1[1].append(Controls.entry.get())
        for Controls.entry in l[1]:
            q1[1].append(Controls.entry.get())
        for Controls.entry in k[2]:
            p1[2].append(Controls.entry.get())
        for Controls.entry in l[2]:
            q1[2].append(Controls.entry.get())
        for Controls.entry in k[3]:
            p1[3].append(Controls.entry.get())
        for Controls.entry in l[3]:
            q1[3].append(Controls.entry.get())
            
        s1 = numpy.column_stack((p1[0],p1[1],p1[2],p1[3]))
        t1 = numpy.column_stack((q1[0],q1[1],q1[2],q1[3]))
        u1 = numpy.concatenate((s1,t1))
        v1 = numpy.concatenate((gamma,u1))
        
        timestr = time.strftime("%Y%m%d-%H%M%S")

        if len(dict['URA'+str(4)].get()) != 0:
            uraname.set(str(dict['URA'+str(4)].get()))

        if len(dict['Intersection Name'+str(4)].get()) != 0:
            intersectionname.set(str(dict['Intersection Name'+str(4)].get()))

        if len(dict['Lane #'+str(6)].get()) != 0:
            uraname.set(str(dict['Lane #'+str(6)].get()))
                
        csvname = 'P_'+str(intersectionname.get())+'_'+str(w1.get())+'_'+str(w2.get())+'_'+str(lanenumber.get())+'_'+timestr+'_'+str(uraname.get())+'.csv'
        #print csvname
            
        with open(csvname, "w") as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for lists in v1:
                writer.writerow(lists)      
    
def timestamp_vid2(win):
    timestamp_2 = Player2.player2.get_time()
    
    timestamp2.set(msToHMS(timestamp_2))
    #print str(timestamp2.get())

    counter2.set(counter2.get()+1)
    #print counter2.get()
    
    for r in range (3,29):
        if len(dict['Time - Video 2'+'28'].get()) == 0:
            if len(dict['Time - Video 2'+str(r)].get()) == 0:
                dict['Time - Video 2'+str(r)].insert(0,str(timestamp2.get()))
                break
            else:
                continue
        else:
            if len(dict['Time - Video 2 (2)'+str(r)].get()) == 0:
                dict['Time - Video 2 (2)'+str(r)].insert(0,str(timestamp2.get()))
                break
            else:
                continue

    if (counter2.get()== 10 or counter2.get() ==20 or counter2.get() ==30 or counter2.get() ==40 or counter2.get()==50):
##    if (len(dict['Time - Video 2'+str(7)].get()) != 0 or len(dict['Time - Video 2'+str(12)].get()) != 0 or
##    len(dict['Time - Video 2'+str(17)].get()) != 0 or len(dict['Time - Video 2'+str(22)].get()) != 0 or
##    len(dict['Time - Video 2 (2)'+str(7)].get()) or len(dict['Time - Video 2 (2)'+str(12)].get())
##    or len(dict['Time - Video 2 (2)'+str(17)].get()) or len(dict['Time - Video 2 (2)'+str(22)].get())):
##        print "x"
        p2 = [[],[],[],[]]
        q2 =[[],[],[],[]]
        for Controls.entry in k[0]:
            p2[0].append(Controls.entry.get())
        for Controls.entry in l[0]:
            q2[0].append(Controls.entry.get())
        for Controls.entry in k[1]:
            p2[1].append(Controls.entry.get())
        for Controls.entry in l[1]:
            q2[1].append(Controls.entry.get())
        for Controls.entry in k[2]:
            p2[2].append(Controls.entry.get())
        for Controls.entry in l[2]:
            q2[2].append(Controls.entry.get())
        for Controls.entry in k[3]:
            p2[3].append(Controls.entry.get())
        for Controls.entry in l[3]:
            q2[3].append(Controls.entry.get())
            
        s2 = numpy.column_stack((p2[0],p2[1],p2[2],p2[3]))
        t2 = numpy.column_stack((q2[0],q2[1],q2[2],q2[3]))
        u2 = numpy.concatenate((s2,t2))
        v2 = numpy.concatenate((gamma,u2))

        timestr = time.strftime("%Y%m%d-%H%M%S")


        if len(dict['URA'+str(4)].get()) != 0:
            uraname.set(str(dict['URA'+str(4)].get()))

        if len(dict['Intersection Name'+str(4)].get()) != 0:
            intersectionname.set(str(dict['Intersection Name'+str(4)].get()))

        if len(dict['Lane #'+str(6)].get()) != 0:
            intersectionname.set(str(dict['Lane #'+str(6)].get()))
                
        csvname = 'P_'+str(intersectionname.get())+'_'+str(w1.get())+'_'+str(w2.get())+'_'+str(lanenumber.get())+'_'+timestr+'_'+str(uraname.get())+'.csv'
        #print csvname
            
        with open(csvname, "w") as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for lists in v2:
                writer.writerow(lists)    
            

def blocking():
    for r in range (3,29):
        if len(dict['Vehicle Type'+'27'].get()) == 0:
            if len(dict['Vehicle Type'+str(r)].get()) == 0:
                dict['Vehicle Type'+str(r)].insert(0,'Blocking')
                break
            else:
                continue
        else:
            if len(dict['Vehicle Type (2)'+str(r)].get()) == 0:
                dict['Vehicle Type (2)'+str(r)].insert(0,'Blocking')
                break
            else:
                continue

def nonblocking():
    for r in range (3,29):
        if len(dict['Vehicle Type'+'27'].get()) == 0:
            if len(dict['Vehicle Type'+str(r)].get()) == 0:
                dict['Vehicle Type'+str(r)].insert(0,'Non Blocking')
                break
            else:
                continue
        else:
            if len(dict['Vehicle Type (2)'+str(r)].get()) == 0:
                dict['Vehicle Type (2)'+str(r)].insert(0,'Non Blocking')
                break
            else:
                continue

def none():
    for r in range (3,29):
        if len(dict['Vehicle Type'+'27'].get()) == 0:
            if len(dict['Vehicle Type'+str(r)].get()) == 0:
                dict['Vehicle Type'+str(r)].insert(0,'None')
                break
            else:
                continue
        else:
            if len(dict['Vehicle Type (2)'+str(r)].get()) == 0:
                dict['Vehicle Type (2)'+str(r)].insert(0,'None')
                break
            else:
                continue
            
def OnStop(win):
    """Stop the player.
    """
    win.player1.stop()
    # reset the time slider
    win.timeslider1.set(0)

def OnStop2(win):
    """Stop the player.
    """
    win.player2.stop()
    # reset the time slider
    win.timeslider2.set(0)
    
def OnStop3():
    """Stop the player.
    """
    Player.player1.stop()
    Player2.player2.stop()
    
def OnExit(win):
    """Closes the window.
    """
    win.Close()

def OnOpen(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w1.set(str(filename)[:-4])
        #print str(w1.get())
        win.parent.title(str(w1.get())+"Video 1")
        # Creation
        win.Media1 = win.Instance1.media_new(str(os.path.join(dirname, filename)))
        win.player1.set_media(win.Media1)

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player1.set_hwnd(win.GetHandle())
        else:
            win.player1.set_xwindow(win.GetHandle()) # this line messes up windows

        # FIXME: this should be made cross-platform
        win.OnPlay()

def OnFastOpen(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w1.set(str(filename)[:-4])
        #print str(w1.get())
        win.parent.title(str(w1.get())+"Video 1")
        # Creation
        win.Media1 = win.Instance1.media_new(str(os.path.join(dirname, filename)))
        win.player1.set_media(win.Media1)
        #win.player1.set_rate(win,10)
        #print win.player1.get_rate()

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player1.set_hwnd(win.GetHandle())
        else:
            win.player1.set_xwindow(win.GetHandle()) # this line messes up windows

        # FIXME: this should be made cross-platform
        win.OnFastPlay()

def OnSlowOpen(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w1.set(str(filename)[:-4])
        #print str(w1.get())
        win.parent.title(str(w1.get())+"Video 1")
        # Creation
        win.Media1 = win.Instance1.media_new(str(os.path.join(dirname, filename)))
        win.player1.set_media(win.Media1)
        #win.player1.set_rate(win,10)
        #print win.player1.get_rate()

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player1.set_hwnd(win.GetHandle())
        else:
            win.player1.set_xwindow(win.GetHandle()) # this line messes up windows

        # FIXME: this should be made cross-platform
        win.OnSlowPlay()

def OnOpen2(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop2()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w2.set(str(filename)[:-4])
        #print str(w2.get())
        win.parent.title(str(w2.get())+"Video 2")
        # Creation
        win.Media2 = win.Instance2.media_new(str(os.path.join(dirname, filename)))
        win.player2.set_media(win.Media2)

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player2.set_hwnd(win.GetHandle2())
        else:
            win.player2.set_xwindow(win.GetHandle2()) # this line messes up windows
        # FIXME: this should be made cross-platform
        win.OnPlay2()

def OnFastOpen2(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w2.set(str(filename)[:-4])
        #print str(w2.get())
        win.parent.title(str(w2.get())+"Video 2")
        # Creation
        win.Media2 = win.Instance2.media_new(str(os.path.join(dirname, filename)))
        win.player2.set_media(win.Media1)
        #win.player1.set_rate(win,10)
        #print win.player1.get_rate()

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player2.set_hwnd(win.GetHandle())
        else:
            win.player2.set_xwindow(win.GetHandle()) # this line messes up windows

        # FIXME: this should be made cross-platform
        win.OnFastPlay2()

def OnSlowOpen2(win):
    """Pop up a new dialow window to choose a file, then play the selected file.
    """
    # if a file is already running, then stop it.
    win.OnStop()

    # Create a file dialog opened in the current home directory, where
    # you can display all kind of files, having as title "Choose a file".
    p = pathlib.Path(os.path.expanduser("~"))
    fullname =  tkFileDialog.askopenfilename(initialdir = p, title = "choose your file",filetypes = (("all files","*.*"),("mp4 files","*.mp4")))
    if os.path.isfile(fullname):
        #print (fullname)
        splt = os.path.split(fullname)
        dirname  = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        w2.set(str(filename)[:-4])
        #print str(w2.get())
        win.parent.title(str(w2.get())+"Video 2")
        # Creation
        win.Media2 = win.Instance2.media_new(str(os.path.join(dirname, filename)))
        win.player2.set_media(win.Media1)
        #win.player1.set_rate(win,10)
        #print win.player1.get_rate()

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            win.player2.set_hwnd(win.GetHandle())
        else:
            win.player2.set_xwindow(win.GetHandle()) # this line messes up windows

        # FIXME: this should be made cross-platform
        win.OnSlowPlay2()

def OnPlay(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    global running1
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player1.get_media():
        win.OnOpen()
    else:
        # Try to launch the media, if this fails display an error message
        win.player1.pause()
        win.player1.set_rate(1)
        
        running1 = True
        #print win.player1.get_rate()
        if win.player1.play() == -1:
            win.errorDialog("Unable to play.")

def OnFastPlay(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player1.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        win.OnFastOpen()
        
    else:
        # Try to launch the media, if this fails display an error message
        win.player1.set_rate(2)
        #print win.player1.get_rate()
        global running1
        running1 = True
        if win.player1.play() == -1:
            win.errorDialog("Unable to play.")

def OnSlowPlay(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player1.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        win.OnSlowOpen()
        
    else:
        # Try to launch the media, if this fails display an error message
        win.player1.set_rate(0.5)
        #print win.player1.get_rate()
        global running1
        running1 = True
        if win.player1.play() == -1:
            win.errorDialog("Unable to play.")


def OnPlay2(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    global running2
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player2.get_media():
        win.OnOpen2()
    else:
        win.player2.pause()
        win.player2.set_rate(1)
        #print win.player2.get_rate()
        running2 = True
        if win.player2.play() == -1:
            win.errorDialog("Unable to play.")

def OnFastPlay2(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player2.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        win.OnFastOpen2()
        
    else:
        # Try to launch the media, if this fails display an error message
        win.player2.set_rate(2)
        #print win.player2.get_rate()
        global running2
        running2 = True
        if win.player2.play() == -1:
            win.errorDialog("Unable to play.")

def OnSlowPlay2(win):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not win.player2.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        win.OnSlowOpen2()
        
    else:
        # Try to launch the media, if this fails display an error message
        win.player2.set_rate(0.5)
        #print win.player2.get_rate()
        global running2
        running2 = True
        if win.player2.play() == -1:
            win.errorDialog("Unable to play.")

def OnPlay3():
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    global running1
    global running2

    if not Player.player1.get_media():
        #win.OnOpen()
        pass
    else:
        # Try to launch the media, if this fails display an error message
        Player.player1.pause()
        Player.player1.set_rate(1)
        
        running1 = True
        #print win.player1.get_rate()
        if Player.player1.play() == -1:
            Player.errorDialog("Unable to play.")
            
    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not Player2.player2.get_media():
        #Player2.OnOpen2()
        pass
    else:
        Player2.player2.pause()
        Player2.player2.set_rate(1)
        #print win.player2.get_rate()
        running2 = True
        if Player2.player2.play() == -1:
            Player2.errorDialog("Unable to play.")

def OnFastPlay3():
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    if not Player.player1.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        #Player.OnFastOpen()
        pass
        
    else:
        # Try to launch the media, if this fails display an error message
        Player.player1.set_rate(2)
        #print win.player2.get_rate()
        global running1
        running1 = True
        if Player.player1.play() == -1:
            Player.errorDialog("Unable to play.")


    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not Player2.player2.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        #Player2.OnFastOpen2()
        pass
        
    else:
        # Try to launch the media, if this fails display an error message
        Player2.player2.set_rate(2)
        #print win.player2.get_rate()
        global running2
        running2 = True
        if Player2.player2.play() == -1:
            Player2.errorDialog("Unable to play.")

def OnSlowPlay3():
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """
    if not Player.player1.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        #Player.OnFastOpen()
        pass
        
    else:
        # Try to launch the media, if this fails display an error message
        Player.player1.set_rate(0.5)
        #print win.player2.get_rate()
        global running1
        running1 = True
        if Player.player1.play() == -1:
            Player.errorDialog("Unable to play.")

    # check if there is a file to play, otherwise open a
    # Tk.FileDialog to select a file
    if not Player2.player2.get_media():
##        win.player1.set_rate(win,10)
##        win.player.get_rate()
        #win.OnSlowOpen2()
        pass
        
    else:
        # Try to launch the media, if this fails display an error message
        Player2.player2.set_rate(0.5)
        #print win.player2.get_rate()
        global running2
        running2 = True
        if Player2.player2.play() == -1:
            Player2.errorDialog("Unable to play.")


def OnSpacePlay3(event=None):
    """Toggle the status to Play/Pause.
    If no file is loaded, open the dialog window.
    """

    global running1
    global running2
    if running1 == False:
        #print "x1"
        running1 = True   
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not Player.player1.get_media():
           # Player.OnOpen()
           pass
        else:
            # Try to launch the media, if this fails display an error message
            if Player.player1.play() == -1:
                Player.errorDialog("Unable to play.")
                
    if running2 == False:
        running2 = True
        if not Player2.player2.get_media():
            #Player2.OnOpen2()
            pass
        else:
            # Try to launch the media, if this fails display an error message
            if Player2.player2.play() == -1:
                Player2.errorDialog("Unable to play.")
                

def OnPause(win):
    """Pause the player.
    """
    global running1
    if running1 == True:
        running1 = False
        #print running1
        win.player1.pause()

def OnPause2(win):
    """Pause the player.
    """
    global running2
    if running2 == True:
        running2 = False
        #print running2
        win.player2.pause()

def OnPause3(event=None):
    """Pause the player.
    """
    global running1
    global running2
    
    if running1 == True:
##        print "x1"
##        print running1
        running1 = False
        Player.player1.pause()
        
    if running2 == True:
        running2 = False
        Player2.player2.pause()

    elif running1 == False and running2 == False:
##        print "x"
        running1 = True
        running2 = True
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not Player.player1.get_media():
           # Player.OnOpen()
           pass
        else:
            # Try to launch the media, if this fails display an error message
            if Player.player1.play() == -1:
                Player.errorDialog("Unable to play.")

        if not Player2.player2.get_media():
            #Player2.OnOpen2()
            pass
        else:
            # Try to launch the media, if this fails display an error message
            if Player2.player2.play() == -1:
                Player2.errorDialog("Unable to play.")
        

def OnSpacePause(event=None):
    """Pause the player.
    """
    global running1
    
    if running1 == True: 
        running1 = False
        Player.player1.pause()

def OnSpacePause2(event=None):
    """Pause the player.
    """
    global running2
        
    if running2 == True:
        running2 = False
        Player2.player2.pause()
        
def errorDialog(win):
    """Display a simple error dialog.
    """
    edialog = Tk.tkMessageBox.showerror(win, 'Error', errormessage)


def Tk_get_root():
    if not hasattr(Tk_get_root, "root"): #(1)
        Tk_get_root.root= Tk.Tk()  #initialization call is inside the function
    return Tk_get_root.root
        
def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)


def on_button(win):
    win.cus_skip = int(win.entry.get())
    print(win.entry.get())


def forskip(win):
    "skip to customized seconds later"
    if len(dict['Custom Skip'+str(1)].get()) != 0:
        customskip.set(int(dict['Custom Skip'+str(1)].get()))
    else:
        customskip.set(10)

##    print customskip.get()

    skip = Player.player1.get_time()
##    print skip

    skip2 = Player2.player2.get_time()
##    print skip2

    fin_skip = int(skip) + (customskip.get())*1000
    fin_skip2 = int(skip2) + (customskip.get())*1000

    i_time = (fin_skip)
    Player.player1.set_time(i_time)

    i_time2 = (fin_skip2)
    Player2.player2.set_time(i_time2)


def backskip(win):
    "skip to customized seconds later"

    if len(dict['Custom Skip'+str(1)].get()) != 0:
        customskip.set(int(dict['Custom Skip'+str(1)].get()))
    else:
        customskip.set(10)

##    print customskip.get()
    
    skip = Player.player1.get_time()
##    print skip

    skip2 = Player2.player2.get_time()
##    print skip2

    fin_skip = int(skip) - (customskip.get())*1000
    fin_skip2 = int(skip2) - (customskip.get())*1000

    i_time = (fin_skip)
    Player.player1.set_time(i_time)

    i_time2 = (fin_skip2)
    Player2.player2.set_time(i_time2)

def forskip1(win):
    "skip to customized seconds later"
    if win.entry.get()!=0:
        customskip1.set(win.entry.get())
    else:
        customskip1.set(10)

##    print customskip1.get()

    skip = Player.player1.get_time()
##    print skip

##    skip2 = Player2.player2.get_time()
##    print skip2

    fin_skip = int(skip) + (customskip1.get())*1000
##    fin_skip2 = int(skip2) + (customskip.get())*1000

    i_time = (fin_skip)
    Player.player1.set_time(i_time)

##    i_time2 = (fin_skip2)
##    Player2.player2.set_time(i_time2)


def backskip1(win):
    "skip to customized seconds later"

    if win.entry.get()!=0:
        customskip1.set(win.entry.get())
    else:
        customskip1.set(10)

##    print customskip1.get()
    
    skip = Player.player1.get_time()
##    print skip

##    skip2 = Player2.player2.get_time()
##    print skip2

    fin_skip = int(skip) - (customskip1.get())*1000
##    fin_skip2 = int(skip2) - (customskip.get())*1000

    i_time = (fin_skip)
    Player.player1.set_time(i_time)

##    i_time2 = (fin_skip2)
##    Player2.player2.set_time(i_time2)

def forskip2(win):
    "skip to customized seconds later"
    if win.entry.get()!=0:
        customskip2.set(win.entry.get())
    else:
        customskip2.set(10)

##    print customskip2.get()

##    skip = Player.player1.get_time()
##    print skip

    skip2 = Player2.player2.get_time()
##    print skip2

##    fin_skip = int(skip) + (customskip.get())*1000
    fin_skip2 = int(skip2) + (customskip2.get())*1000

##    i_time = (fin_skip)
##    Player.player1.set_time(i_time)

    i_time2 = (fin_skip2)
    Player2.player2.set_time(i_time2)


def backskip2(win):
    "skip to customized seconds later"

    if win.entry.get()!=0:
        customskip2.set(win.entry.get())
    else:
        customskip2.set(10)

##    print customskip2.get()
    
##    skip = Player.player1.get_time()
##    print skip

    skip2 = Player2.player2.get_time()
##    print skip2

##    fin_skip = int(skip) - (customskip.get())*1000
    fin_skip2 = int(skip2) - (customskip2.get())*1000

##    i_time = (fin_skip)
##    Player.player1.set_time(i_time)

    i_time2 = (fin_skip2)
    Player2.player2.set_time(i_time2)

if __name__ == "__main__":
    # Create a Tk.App(), which handles the windowing system event loop
    root = Tk_get_root()
    #root2 = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)
    player = Player(root)
    
    sub_window = Tk.Toplevel(root)
    player2 = Player2(sub_window)
    #Tk.Label(sub_window, text = "This is the other window").pack()

    another_window = Tk.Toplevel(root)
    sync = Controls(another_window)

    # show the player window centred and run the application
    root.mainloop()


