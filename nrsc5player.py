import logging
import os
import queue
import threading
import pyaudio
import numpy
import nrsc5


class NRSC5player:

    def __init__(self):
        if os.name == "nt":
            os.add_dll_directory(os.getcwd())
        self.radio = nrsc5.NRSC5(
            lambda evt_type, evt: self.callback(evt_type, evt))
        self.audio_queue = queue.Queue(maxsize=64)
        self.device_condition = threading.Condition()
        self.frequency = 0
        self.program = 0
        self.deviceid = 0
        self.host = None

        self.programs = {}
        self.logos = {}

        self.logoportmap = {}
        self.imageportmap = {}

        self.artist = None
        self.title = None
        self.album = None
        self.xhdr = {}
        self.albumart = {}
        self.albumartindex = {}

        self.station = None
        self.slogan = None

        self.volume = 1.0

        self._playing = False

    def callback(self, evt_type, evt):

        if evt_type == nrsc5.EventType.LOST_DEVICE:
            logging.info("Lost device")
            self.ui.setstatus("Lost device")
            with self.device_condition:
                self.device_condition.notify()
        elif evt_type == nrsc5.EventType.SYNC:
            logging.info("Synchronized")
            self.ui.setstatus("Synchronized")
        elif evt_type == nrsc5.EventType.LOST_SYNC:
            logging.info("Lost synchronization")
            self.ui.setstatus("Lost synchronization")

        elif evt_type == nrsc5.EventType.AUDIO:
            if evt.program == self.program:
                self.audio_queue.put(evt.data)

        elif evt_type == nrsc5.EventType.ID3:
            if evt.program == self.program:
                if evt.title and evt.title != self.title:
                    self.title = evt.title
                    self.ui.settitle(evt.title)
                    logging.info("Title: %s", evt.title)
                if evt.artist and evt.artist != self.artist:
                    self.artist = evt.artist
                    self.ui.setartist(evt.artist)
                    logging.info("Artist: %s", evt.artist)
                if evt.album and evt.album != self.album:
                    self.album = evt.album
                    logging.info("Album: %s", evt.album)
                if evt.genre:
                    self.genre = evt.genre
                    logging.info("Genre: %s", evt.genre)
                if evt.ufid:
                    self.ufid = evt.ufid
                    logging.info("Unique file identifier: %s %s",
                                 evt.ufid.owner, evt.ufid.id)

            #pull albumart from library and assign to albumartindex
            if evt.xhdr and (evt.program not in self.xhdr
                             or evt.xhdr != self.xhdr[evt.program]):
                self.xhdr[evt.program] = evt.xhdr
                logging.info("XHDR: param=%s mime=%s lot=%s", evt.xhdr.param,
                             evt.xhdr.mime, evt.xhdr.lot)

                #garbage collection?
                if evt.program in self.albumartindex and self.albumartindex[
                        evt.program] in self.albumart:
                    del self.albumart[self.albumartindex[evt.program]]

                self.albumartindex[evt.program] = evt.xhdr.lot

                self.updatealbumart(self.program)

        elif evt_type == nrsc5.EventType.SIG:
            for service in evt:
                logging.info("SIG Service: type=%s number=%s name=%s",
                             service.type, service.number, service.name)
                if service.type == nrsc5.ServiceType.AUDIO:
                    index = service.number - 1
                    self.programs[index] = service.name
                    self.ui.setprogrambutton(index, service.name)
                    if index == self.program:
                        self.ui.setprogramname(service.name)
                    for component in service.components:
                        #audio data
                        if component.type == nrsc5.ComponentType.AUDIO:
                            logging.info(
                                "  Audio component: id=%s port=%04X type=%s mime=%s",
                                component.id, component.audio.port,
                                component.audio.type, component.audio.mime)
                        #map ports to programs
                        elif component.type == nrsc5.ComponentType.DATA:
                            if component.data.mime == nrsc5.MIMEType.PRIMARY_IMAGE:
                                self.imageportmap[component.data.port] = index
                            if component.data.mime == nrsc5.MIMEType.STATION_LOGO:
                                self.logoportmap[component.data.port] = index
                            logging.info(
                                "  Data component: id=%s port=%04X service_data_type=%s type=%s mime=%s",
                                component.id, component.data.port,
                                component.data.service_data_type,
                                component.data.type, component.data.mime)

        elif evt_type == nrsc5.EventType.LOT:
            logging.info("LOT file: port=%04X lot=%s name=%s size=%s mime=%s",
                         evt.port, evt.lot, evt.name, len(evt.data), evt.mime)

            #load image into library.  there may be a cleaner way to index logos and art...
            programindex = None
            if evt.port in self.logoportmap:
                programindex = self.logoportmap[evt.port]
                if programindex not in self.logos:  #probably don't need to set more than once
                    self.logos[programindex] = evt.data
                    logging.info("Program Logo %s: %s", programindex, evt.name)
            elif evt.port in self.imageportmap:
                programindex = self.imageportmap[evt.port]
                if evt.lot not in self.albumart:  #probably don't need to set more than once
                    self.albumart[evt.lot] = evt.data

            if programindex is not None and programindex == self.program:
                self.updatealbumart(self.program)

        elif evt_type == nrsc5.EventType.SIS:
            if evt.name and self.station != evt.name:
                self.station = evt.name
                self.ui.setstationname(evt.name)
                logging.info("Station name: %s", evt.name)
            if evt.slogan and self.slogan != evt.slogan:
                self.slogan = evt.slogan
                self.ui.setslogan(evt.slogan)
                logging.info("Slogan: %s", evt.slogan)

    def setprogram(self, programindex):
        if programindex != self.program and programindex in self.programs:
            with self.audio_queue.mutex:
                self.audio_queue.queue.clear()
            self.program = programindex
            self.ui.setprogramname(self.programs[programindex])
            self.updatealbumart(self.program)

    def setvolume(self, volume):
        self.volume = volume

    def updatealbumart(self, programindex):
        if programindex in self.albumartindex and self.albumartindex[
                programindex] in self.albumart:
            self.ui.setalbumartdata(
                self.albumart[self.albumartindex[programindex]])
        elif programindex in self.logos:
            self.ui.setalbumartdata(self.logos[programindex])
        else:
            self.ui.setalbumartdata(None)
            logging.info("No current album art selected and no logo stored?")

    def run(self):
        logging.basicConfig(level=10,
                            format="%(asctime)s %(message)s",
                            datefmt="%H:%M:%S")

        try:
            if self.host != None:
                host = self.host
                port = "1234"
                if ':' in host:
                    host, port = host.split(':')
                logging.info("Connecting to host %s port %s", host, port)
                self.ui.setstatus("Connecting to host %s port %s", host, port)
                self.radio.open_rtltcp(host, port)
            else:
                logging.info("Connecting to device %s", self.deviceid)
                self.ui.setstatus("Connecting to device %s", self.deviceid)
                self.radio.open(self.deviceid)
            self.radio.set_frequency(self.frequency)

            self._playing = True

            self.audio_thread = threading.Thread(target=self.audio_worker)
            self.audio_thread.start()

            self.radio.start()

        except nrsc5.NRSC5Error as error:
            logging.info("Error: %s", str(error))
            self.ui.setstatus("Error: %s", str(error))
            
        logging.info("Tuning %s", self.frequency)
        self.ui.setstatus("Tuning %s", self.frequency)


    def stop(self):
        self.ui.setstatus("Stopping")
        logging.info("Stopping")
        if self._playing == True:
            self._playing = False
            logging.info("self._playing = False")
            self.radio.stop()
            logging.info("self.radio.stop()")
            self.radio.set_bias_tee(0)
            logging.info("self.radio.set_bias_tee(0)")
            self.radio.close()
            logging.info("self.radio.close()")

        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
            logging.info("self.audio_queue.queue.clear()")

        self.audio_thread.join()

        self.ui.setstatus("Stopped")
        logging.info("Stopped")

    def audio_worker(self):
        audio = pyaudio.PyAudio()
        try:
            index = audio.get_default_output_device_info()["index"]
            stream = audio.open(format=pyaudio.paInt16,
                                channels=2,
                                rate=44100,
                                output_device_index=index,
                                output=True)
        except OSError:
            logging.warning("No audio output device available.")
            stream = None

        while self._playing:
            samples = self.audio_queue.get()
            if samples is None:
                break
            if stream:
                stream.write(samples)
            self.audio_queue.task_done()

        if stream:
            stream.stop_stream()
            stream.close()
        audio.terminate()

        logging.info("Worker Stopped")
