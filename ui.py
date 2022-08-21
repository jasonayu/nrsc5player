#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import nrsc5player
import configparser

class MusicPlayer:

    def __init__(self):

        self.root = Tk()

        self.style = ttk.Style(self.root)
        #self.style.theme_use("vista")

        self.config = configparser.ConfigParser()

        self.windowtitle = "NRSC5 HD Radio"

        self.info = {}
        self.info['title'] = 'title'
        self.info['artist'] = "artist"
        self.info['program'] = "program"
        self.info['station'] = "station"
        self.info['slogan'] = "slogan"
        self.status = None

        self.player = nrsc5player.NRSC5player()
        self.player.ui = self

        self.root.title(self.windowtitle)
        self.root.geometry("600x400")

        self.defaultimage = ImageTk.PhotoImage(
            Image.new('RGB', (200, 200), color='gray'))

        self.albumartlabel = Label(self.root,
                                   image=self.defaultimage,
                                   width=200,
                                   height=200)
        self.albumartlabel.grid(rowspan=6, row=0, column=0, padx=5, sticky=W)

        self.infolabel = {}
        self.infolabel['title'] = ttk.Label(self.root,
                                            text=self.info['title'],
                                            font=("Arial", 12))
        self.infolabel['title'].grid(row=0, column=1, padx=0, sticky=W)

        self.infolabel['artist'] = ttk.Label(self.root,
                                             text=self.info['artist'],
                                             font=("Arial", 12))
        self.infolabel['artist'].grid(row=1, column=1, padx=0, sticky=W)

        self.infolabel['program'] = ttk.Label(self.root,
                                              text=self.info['program'],
                                              font=("Arial", 12))
        self.infolabel['program'].grid(row=2, column=1, padx=0, sticky=W)

        self.infolabel['station'] = ttk.Label(self.root,
                                              text=self.info['station'],
                                              font=("Arial", 12))
        self.infolabel['station'].grid(row=3, column=1, padx=0, sticky=W)

        self.infolabel['slogan'] = ttk.Label(self.root,
                                             text=self.info['slogan'],
                                             font=("Arial", 12))
        self.infolabel['slogan'].grid(row=4, column=1, padx=0, sticky=W)

        self.freqvar = StringVar()
        freqentry = ttk.Spinbox(self.root,
                              textvariable=self.freqvar,
                              from_=87.5,
                              to=107.9,
                              increment=0.2,
                              wrap=False)
        freqentry.grid(row=5, column=1, padx=0, sticky=W)
        freqentry.bind('<Return>', self.freqreturn)

        ttk.Button(self.root, text="Start", command=self.play).grid(row=5,
                                                                    column=2,
                                                                    padx=5,
                                                                    sticky=W)
        ttk.Button(self.root, text="Stop", command=self.stop).grid(row=5,
                                                                   column=3,
                                                                   padx=5,
                                                                   sticky=W)

        self.hostvar = StringVar()
        ttk.Entry(self.root, textvariable=self.hostvar).grid(row=6,
                                                             column=1,
                                                             padx=0,
                                                             pady=5,
                                                             sticky=W)

        self.programbtn = {}
        self.programbtn[0] = ttk.Button(self.root,
                                        command=lambda: self.setprogram(0))
        self.programbtn[0].grid(row=7, column=1, padx=5, sticky=W)
        self.programbtn[1] = ttk.Button(self.root,
                                        command=lambda: self.setprogram(1))
        self.programbtn[1].grid(row=8, column=1, padx=5, sticky=W)
        self.programbtn[2] = ttk.Button(self.root,
                                        command=lambda: self.setprogram(2))
        self.programbtn[2].grid(row=9, column=1, padx=5, sticky=W)
        self.programbtn[3] = ttk.Button(self.root,
                                        command=lambda: self.setprogram(3))
        self.programbtn[3].grid(row=10, column=1, padx=5, sticky=W)

        self.statuslabel = ttk.Label(self.root,
                                     text=self.status,
                                     font=("Arial", 12))
        self.statuslabel.grid(row=11, column=1, padx=0, sticky=W)

        self.volumevar = IntVar()
        self.volumevar.set(100)
        self.volumeslider = ttk.Scale(self.root,
                                      from_=0,
                                      to=100,
                                      orient='horizontal',
                                      variable=self.volumevar,
                                      command=self.setvolume)
        self.volumeslider.grid(row=12, column=1, padx=0, sticky=W)
        self.volumelabel = ttk.Label(self.root,
                                     text=self.volumevar.get(),
                                     font=("Arial", 12))
        self.volumelabel.grid(row=13, column=1, padx=0, sticky=W)

        self.root.protocol("WM_DELETE_WINDOW", self.onclose)

        self.loadconfig()
        self.resetdisplay()

        self.root.mainloop()

    def freqreturn(self, event):
        self.play()

    def updatewindowtitle(self):
        titleparts = []
        if self.player != None:
            if self.info['artist'] != None:
                titleparts.append(self.info['artist'])
            if self.info['title'] != None:
                titleparts.append(self.info['title'])
            if len(titleparts) < 1 and self.info['program'] != None:
                titleparts.append(self.info['program'])
            if len(titleparts) < 1 and self.info['station'] != None:
                titleparts.append(self.info['station'])
                if self.info['slogan'] != None:
                    titleparts.append(self.info['slogan'])
        titleparts.append(self.windowtitle)
        self.root.title(" - ".join(titleparts))

    def settitle(self, input):
        self.info['title'] = input
        self.infolabel['title'].config(text=input)
        self.updatewindowtitle()

    def setartist(self, input):
        self.info['artist'] = input
        self.infolabel['artist'].config(text=input)
        self.updatewindowtitle()

    def setprogramname(self, input):
        self.info['program'] = input
        self.infolabel['program'].config(text=input)
        self.updatewindowtitle()

    def setstationname(self, input):
        self.info['station'] = input
        self.infolabel['station'].config(text=input)
        self.updatewindowtitle()

    def setslogan(self, input):
        self.info['slogan'] = input
        self.infolabel['slogan'].config(text=input)
        self.updatewindowtitle()

    def setalbumart(self, newalbumart):
        self.root.img = ImageTk.PhotoImage(Image.open(newalbumart))
        self.albumartlabel.configure(image=self.root.img)

    def setalbumartdata(self, imagedata):
        if imagedata is not None:
            self.root.img = ImageTk.PhotoImage(data=imagedata)
        else:
            self.root.img = self.defaultimage
        self.albumartlabel.configure(image=self.root.img)

    def setprogrambutton(self, id, name):
        self.programbtn[id].config(state="normal", text=name)

    def resetdisplay(self):
        for id in self.info:
            self.info[id] = None
        for id in self.infolabel:
            self.infolabel[id].config(text=id)  #todo?
        self.root.img = self.defaultimage
        self.albumartlabel.configure(image=self.root.img)
        for id in self.programbtn:
            btntext = "Program", id + 1
            self.programbtn[id].config(state="disabled", text=btntext)
        self.updatewindowtitle()

    def setstatus(self, input, *args):
        self.status = input % args
        self.statuslabel.config(text=input)

    def setprogram(self, prog):
        self.player.setprogram(prog)

    def setvolume(self, event):
        self.volumelabel.configure(text=self.volumevar.get())
        if self.player:
            self.player.setvolume(self.volumevar.get() * 0.01)

    def loadconfig(self):
        self.config.read('config.ini')
        if 'volume' in self.config['DEFAULT']:
            self.volumevar.set(self.config['DEFAULT']['volume'])
            self.setvolume(None)
        if 'frequency' in self.config['DEFAULT']:
            self.freqvar.set(self.config['DEFAULT']['frequency'])
        if 'host' in self.config['DEFAULT']:
            self.hostvar.set(self.config['DEFAULT']['host'])

    def saveconfig(self):
        self.config['DEFAULT'] = {
            'volume': self.volumevar.get(),
            'host': self.hostvar.get(),
            'frequency': self.freqvar.get()
        }
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def play(self):
        if self.freqvar.get():
            freq = float(self.freqvar.get())
            if freq and freq < 10000:
                freq *= 1e6
            if self.player.frequency != freq:
                self.stop()
            
            self.saveconfig()
            self.resetdisplay()
            self.player.program = 0
            self.player.frequency = freq
            self.player.volume = self.volumevar.get()
            if self.hostvar.get():
                self.player.host = self.hostvar.get()
            self.player.run()

    def stop(self):
        self.player.stop()
        self.resetdisplay()
        self.updatewindowtitle()

    def onclose(self):
        self.stop()
        self.saveconfig()
        self.root.destroy()


if __name__ == "__main__":
    MusicPlayer()
