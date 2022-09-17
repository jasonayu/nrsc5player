#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import nrsc5service
import configparser
import io

class NRSC5Player:

    def __init__(self, root):

        self.root = root

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        self.config = configparser.ConfigParser()
        self.configwindow = None

        self.windowtitle = "NRSC5 Player"

        self.info = {}
        self.info['title'] = "title"
        self.info['artist'] = "artist"
        self.info['program'] = "program"
        self.info['station'] = "station"
        self.info['slogan'] = "slogan"
        self.status = None

        self.root.title(self.windowtitle)
        #self.root.geometry("640x225")
        self.root.geometry("")
        self.root.resizable(0, 0)

        self.defaultimage = Image.new('RGB', (200, 200), color='gray')

        self.infosection = ttk.Frame(self.root, width=640, height=200)

        self.albumartlabel = ttk.Label(self.infosection,
                                   image=ImageTk.PhotoImage(self.defaultimage))

        self.infotext = ttk.Frame(self.infosection)

        self.infolabel = {}
        self.infolabel['title'] = ttk.Label(self.infotext,
                                            text=self.info['title'],
                                            font=("-size 14"))
        self.infolabel['title'].pack()

        self.infolabel['artist'] = ttk.Label(self.infotext,
                                             text=self.info['artist'],
                                             font=("-size 11"))
        self.infolabel['artist'].pack()

        self.infolabel['program'] = ttk.Label(self.infotext,
                                              text=self.info['program'],
                                              font=("-size 11"))
        self.infolabel['program'].pack()

        self.infolabel['station'] = ttk.Label(self.infotext,
                                              text=self.info['station'],
                                              font=("-size 11"))
        self.infolabel['station'].pack()

        self.infolabel['slogan'] = ttk.Label(self.infotext,
                                             text=self.info['slogan'],
                                             font=("-size 11"))
        self.infolabel['slogan'].pack()

        self.programbar = ttk.Frame(self.infosection)
        self.programbtn = {}
        self.programbtn[0] = ttk.Button(self.programbar,
                                        command=lambda: self.setprogram(0))
        self.programbtn[0].pack(padx=1, expand=True, fill="x", side="left")
        self.programbtn[1] = ttk.Button(self.programbar,
                                        command=lambda: self.setprogram(1))
        self.programbtn[1].pack(padx=1, expand=True, fill="x", side="left")
        self.programbtn[2] = ttk.Button(self.programbar,
                                        command=lambda: self.setprogram(2))
        self.programbtn[2].pack(padx=1, expand=True, fill="x", side="left")
        self.programbtn[3] = ttk.Button(self.programbar,
                                        command=lambda: self.setprogram(3))
        self.programbtn[3].pack(padx=1, expand=True, fill="x", side="left")

        self.controlsection = ttk.Frame(self.infosection)

        ttk.Button(self.controlsection,
                   text="Conf",
                   width=6,
                   command=self.openconfigwindow).pack(side="left",
                                                       padx=(0, 7))

        self.tunerbar = ttk.Frame(self.controlsection)
        ttk.Label(self.tunerbar, text="Frequency:").pack(side="left",
                                                         fill="x",
                                                         padx=(0, 2))
        self.freqvar = tk.StringVar()
        freqentry = ttk.Spinbox(self.tunerbar,
                                textvariable=self.freqvar,
                                from_=87.5,
                                to=107.9,
                                increment=0.2,
                                wrap=False,
                                width=7)
        freqentry.pack(side="left", fill="x", padx=(0, 2))
        freqentry.bind('<Return>', self.freqreturn)
        ttk.Button(self.tunerbar, text="Play", width=6,
                   command=self.play).pack(side="left", fill="x", padx=(0, 2))
        ttk.Button(self.tunerbar, text="Stop", width=6,
                   command=self.stop).pack(side="left", fill="x")
        self.tunerbar.pack(side="left", fill="x", padx=(0, 7))

        self.volumesection = ttk.Frame(self.controlsection)
        self.volumevar = tk.IntVar()
        self.volumevar.set(100)
        self.volumeslider = ttk.Scale(self.volumesection,
                                      from_=0,
                                      to=100,
                                      orient='horizontal',
                                      variable=self.volumevar,
                                      command=self.setvolume)
        self.volumeslider.pack(side="left")
        self.volumelabel = ttk.Label(self.volumesection,
                                     text=self.volumevar.get(),
                                     width=3)
        self.volumelabel.pack(side="left", fill="x", padx=(3, 0))
        self.volumesection.pack(side="left", fill="x", expand=True)

        self.infosection.pack(side="top", fill="x")

        self.infosection.columnconfigure(0, weight=0)
        self.infosection.columnconfigure(1, weight=1)
        self.infosection.rowconfigure(0, weight=1)
        self.infosection.rowconfigure(1, weight=0)
        self.infosection.rowconfigure(2, weight=0)

        self.albumartlabel.grid(rowspan=3, column=0, row=0, sticky=tk.NSEW)
        self.infotext.grid(column=1, row=0, sticky=tk.EW)
        self.programbar.grid(column=1, row=1, sticky=tk.EW, padx=2)
        self.controlsection.grid(column=1, row=2, sticky=tk.S, padx=10, pady=2)

        self.popup_menu = tk.Menu(self.root, tearoff=0)
        self.popup_menu.add_command(label="Configuration",
                                    command=self.openconfigwindow)
        self.popup_menu.add_command(label="Exit", command=self.onclose)

        self.infosection.bind("<Button-3>", self.popup)
        for child in self.infosection.winfo_children():
            child.bind("<Button-3>", self.popup)
        for child in self.infotext.winfo_children():
            child.bind("<Button-3>", self.popup)

        self.programvar = tk.IntVar()
        self.hostvar = tk.StringVar()
        self.devicevar = tk.IntVar()
        self.cachevar = tk.BooleanVar()

        configbar = ttk.Frame(self.root)

        configbar.pack(side="top", fill="x")

        self.statusbar = ttk.Frame(self.root)
        self.statuslabel = ttk.Label(self.statusbar,
                                     text="Disconnected",
                                     relief=tk.SUNKEN,
                                     anchor=tk.W)
        self.statuslabel.pack(fill="both", expand=True)
        self.statusbar.pack(side="bottom", fill="x")

        self.root.protocol("WM_DELETE_WINDOW", self.onclose)
        self.root.update()

        self.service = nrsc5service.NRSC5service()
        self.service.ui = self

        self.loadconfig()
        self.resetdisplay()

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def openconfigwindow(self):
        if self.configwindow is not None:
            return
        self.configwindow = tk.Toplevel(self.root)
        self.configwindow.resizable(0, 0)
        self.configwindow.title("Configuration")

        configframe = ttk.Frame(self.configwindow, borderwidth=10)
        configframe.pack()

        hostvarlabel = ttk.Label(configframe, text="rtl_tcp Host:")
        hostvarlabel.grid(column=0, row=0, padx=2, pady=2, sticky=tk.E)
        hostvarentry = ttk.Entry(configframe, textvariable=self.hostvar)
        hostvarentry.grid(column=1, row=0, pady=2, sticky=tk.W)

        devicevarlabel = ttk.Label(configframe, text="Device ID:")
        devicevarlabel.grid(column=0, row=1, padx=2, sticky=tk.E)
        devicevarentry = ttk.Entry(configframe, textvariable=self.devicevar)
        devicevarentry.grid(column=1, row=1, pady=2, sticky=tk.W)

        cachevarlabel = ttk.Label(configframe, text="Cache Logos:")
        cachevarlabel.grid(column=0, row=2, padx=2, sticky=tk.E)
        cachevarbutton = ttk.Checkbutton(configframe,
                                         text="Enable",
                                         variable=self.cachevar,
                                         onvalue=True,
                                         offvalue=False)
        cachevarbutton.grid(column=1, row=2, pady=2, sticky=tk.W)

        savebutton = ttk.Button(configframe,
                                text="Save",
                                command=self.saveconfigwindow)
        savebutton.grid(columnspan=2, column=0, row=4)

        self.configwindow.protocol("WM_DELETE_WINDOW",
                                   self.onconfigwindowclose)
        self.configwindow.update()

        xoffset = self.root.winfo_x() + (self.root.winfo_width() / 2)
        yoffset = self.root.winfo_y() + (self.root.winfo_height() / 2)
        configoffsetx = self.configwindow.winfo_width() / 2
        configoffsety = self.configwindow.winfo_height() / 2
        xpos = int(xoffset - configoffsetx)
        ypos = int(yoffset - configoffsety)
        self.configwindow.geometry(f"+{xpos}+{ypos}")
        self.configwindow.focus()

    def saveconfigwindow(self):
        self.saveconfig()
        self.onconfigwindowclose()

    def onconfigwindowclose(self):
        self.configwindow.destroy()
        self.configwindow = None

    def freqreturn(self, event):
        self.play()

    def updatewindowtitle(self):
        titleparts = []
        if self.service != None:
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

    def updateinfo(self):
        for id in self.infolabel:
            self.infolabel[id].config(text=self.info[id])
            self.infolabel[id].config(wraplength=self.infotext.winfo_width())
            self.infolabel[id].update_idletasks()
        self.updatewindowtitle()

    def settitle(self, input):
        self.info['title'] = input
        self.updateinfo()

    def setartist(self, input):
        self.info['artist'] = input
        self.updateinfo()

    def setprogramname(self, input):
        self.info['program'] = input
        self.updateinfo()

    def setstationname(self, input):
        self.info['station'] = input
        self.updateinfo()

    def setslogan(self, input):
        self.info['slogan'] = input
        self.updateinfo()

    def setalbumart(self, img):
        wwidth = self.albumartlabel.winfo_width() - 4
        wheight = self.albumartlabel.winfo_height() - 4
        dim = max(wwidth, wheight, 200)
        self.root.img = ImageTk.PhotoImage(img.resize((dim, dim)))
        self.albumartlabel.configure(image=self.root.img)

    def setalbumartfile(self, newalbumart):
        img = Image.open(newalbumart)
        self.setalbumart(img)

    def setalbumartdata(self, imagedata):
        if imagedata is not None:
            img = Image.open(io.BytesIO(imagedata))
        else:
            img = self.defaultimage
        self.setalbumart(img)

    def setprogrambutton(self, id, name):
        maxlength = 13
        if name and len(name) > maxlength:
            name = name[:maxlength - 3] + "..."
        self.programbtn[id].config(state="normal", text=name)

    def resetdisplay(self):
        for id in self.info:
            self.info[id] = None
        for id in self.infolabel:
            self.infolabel[id].config(text="")  #todo?
        self.root.img = self.defaultimage
        for id in self.programbtn:
            btntext = "HD", id + 1
            self.programbtn[id].config(state="disabled", text=btntext)
        self.updatewindowtitle()
        self.setalbumartdata(None)

    def setstatus(self, input, *args):
        self.status = input % args
        self.statuslabel.config(text=self.status)
        self.statuslabel.update_idletasks()

    def setprogram(self, prog):
        self.programvar.set(prog)
        self.service.setprogram(prog)

    def setvolume(self, event):
        self.volumelabel.configure(text=self.volumevar.get())
        if self.service:
            self.service.setvolume(self.volumevar.get() * 0.01)

    def loadconfig(self):
        self.config.read('config.ini')
        if 'frequency' in self.config['DEFAULT']:
            self.freqvar.set(self.config['DEFAULT']['frequency'])
        if 'program' in self.config['DEFAULT']:
            self.programvar.set(self.config['DEFAULT']['program'])
        if 'volume' in self.config['DEFAULT']:
            self.volumevar.set(self.config['DEFAULT']['volume'])
            self.setvolume(None)
        if 'host' in self.config['DEFAULT']:
            self.hostvar.set(self.config['DEFAULT']['host'])
        if 'cache' in self.config['DEFAULT']:
            self.cachevar.set(self.config['DEFAULT']['cache'])

    def saveconfig(self):
        self.config['DEFAULT'] = {
            'frequency': self.freqvar.get(),
            'program': self.programvar.get(),
            'volume': self.volumevar.get(),
            'host': self.hostvar.get(),
            'device': self.devicevar.get(),
            'cache': self.cachevar.get(),
        }
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def play(self):
        try:
            freqvar = float(self.freqvar.get())
        except ValueError:
            return
        changefreq = self.service.frequency != freqvar
        if changefreq or not self.service.playing:
            if self.service.playing:
                self.stop()
            if changefreq and self.service.frequency != 0:
                self.programvar.set(0)
                self.resetdisplay()
            self.service.setfrequency(freqvar)
            self.service.program = self.programvar.get()
            self.service.host = self.hostvar.get()
            self.service.cachelogos = self.cachevar.get()
            self.service.deviceid = self.devicevar.get()
            self.service.run()

    def stop(self):
        self.service.stop()
        #self.resetdisplay()
        #self.updatewindowtitle()

    def onclose(self):
        self.stop()
        self.saveconfig()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    #root.tk.call('tk', 'scaling', 1.0)
    NRSC5Player(root)
    root.mainloop()
