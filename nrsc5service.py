import logging
import os
import queue
import threading
import pyaudio
import numpy
import nrsc5
import sys


class NRSC5service:

    def __init__(self):
        logging.basicConfig(level=20,
                            format="%(asctime)s %(message)s",
                            datefmt="%H:%M:%S")
        if os.name == "nt":
            os.add_dll_directory(os.getcwd())
        self.radio = nrsc5.NRSC5(
            lambda evt_type, evt: self.callback(evt_type, evt))
        self.device_condition = threading.Condition()

        self.deviceid = 0
        self.host = None
        self.volume = 1.0
        self.frequency = 0

        self.bufferlength = 256
        self.bufferthresh = 32

        self.cachelogos = True
        self.aas_dir = None

        self.resetdata()
        self.resetprograms()

        self.playing = False

    def resetprograms(self):
        self.program = 0
        self.programs = {}

    def resetdata(self):
        self.audio_queues = {
            0: queue.Queue(maxsize=self.bufferlength),
            1: queue.Queue(maxsize=self.bufferlength),
            2: queue.Queue(maxsize=self.bufferlength),
            3: queue.Queue(maxsize=self.bufferlength)
        }
        self.buffered = {}
        self.logos = {}
        self.logoportmap = {}
        self.imageportmap = {}
        self.id3 = {}
        self.albumart = {}
        self.station = None
        self.slogan = None
        self.initialbuffer = False

    def exceptioninfo(self, ex):
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logging.info(message)
        return message

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
            if self.playing:
                try:
                    self.audio_queues[evt.program].put(evt.data)
                except Exception as ex:
                    self.exceptioninfo(ex)

            #logging.info("Current: %d, 0: %d, 1: %d, 2: %d, 3: %d",
            #            self.program,
            #            self.audio_queues[0].qsize(),
            #            self.audio_queues[1].qsize(),
            #            self.audio_queues[2].qsize(),
            #            self.audio_queues[3].qsize())

        elif evt_type == nrsc5.EventType.ID3:

            if evt.program not in self.id3 or evt != self.id3[evt.program]:

                # garbage collection?
                if evt.program in self.id3:
                    try:
                        if self.id3[evt.program].xhdr is not None:
                            currentlot = self.id3[evt.program].xhdr.lot
                            if currentlot in self.albumart and currentlot != evt.xhdr.lot:
                                del self.albumart[currentlot]
                    except Exception as ex:
                        self.exceptioninfo(ex)

                self.id3[evt.program] = evt

                if evt.program == self.program:
                    self.updateprograminfo(self.program)
                    self.updatealbumart(self.program)

        elif evt_type == nrsc5.EventType.SIG:
            for service in evt:
                #logging.info("SIG Service: type=%s number=%s name=%s",
                #             service.type, service.number, service.name)
                if service.type == nrsc5.ServiceType.AUDIO:
                    index = service.number - 1
                    if index not in self.programs:
                        self.programs[index] = {}
                    self.programs[index]['name'] = service.name
                    self.ui.setprogrambutton(index, service.name)
                    for component in service.components:
                        #audio data
                        if component.type == nrsc5.ComponentType.AUDIO:
                            continue
                            logging.info(
                                "  Audio component: id=%s port=%04X type=%s mime=%s",
                                component.id, component.audio.port,
                                component.audio.type, component.audio.mime)
                        #map ports to programs
                        elif component.type == nrsc5.ComponentType.DATA:
                            if component.data.mime == nrsc5.MIMEType.PRIMARY_IMAGE:
                                self.imageportmap[component.data.port] = index
                                self.programs[index][
                                    'imageport'] = component.data.port
                            if component.data.mime == nrsc5.MIMEType.STATION_LOGO:
                                self.logoportmap[component.data.port] = index
                                self.programs[index][
                                    'logoport'] = component.data.port
                            continue
                            logging.info(
                                "  Data component: id=%s port=%04X service_data_type=%s type=%s mime=%s",
                                component.id, component.data.port,
                                component.data.service_data_type,
                                component.data.type, component.data.mime)

                    if index == self.program:
                        self.ui.setprogramname(service.name)
                        self.updatealbumart(index)

        elif evt_type == nrsc5.EventType.LOT:
            #logging.info("LOT file: port=%04X lot=%s name=%s size=%s mime=%s",
            #             evt.port, evt.lot, evt.name, len(evt.data), evt.mime)

            #load image into library.  there may be a cleaner way to index logos and art...
            programindex = None
            if evt.port in self.logoportmap:
                programindex = self.logoportmap[evt.port]
                if programindex not in self.logos:  #probably don't need to set more than once
                    self.logos[programindex] = evt.data
                    if self.cachelogos and self.aas_dir is not None:
                        logofilename = str(self.frequency) + '-' + str(
                            programindex)
                        path = os.path.join(self.aas_dir, logofilename)
                        with open(path, "wb") as file:
                            file.write(evt.data)
                            #logging.info("Writing logo %s", logofilename)

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
                #logging.info("Station name: %s", evt.name)
            if evt.slogan and self.slogan != evt.slogan:
                self.slogan = evt.slogan
                self.ui.setslogan(evt.slogan)
                #logging.info("Slogan: %s", evt.slogan)

    def setprogram(self, programindex):
        if programindex != self.program and programindex in self.programs:
            logging.info("Program %s", programindex)
            self.program = programindex
            self.updateprograminfo(self.program)
            self.updatealbumart(self.program)

    def setfrequency(self, frequency):
        if frequency != self.frequency:
            self.resetprograms()
            self.frequency = frequency

    def updateprograminfo(self, programindex):
        if programindex in self.id3:
            title = self.id3[programindex].title
            if title:
                title = title.encode("latin-1").decode("utf-8")
            self.ui.settitle(title)
            artist = self.id3[programindex].artist
            if artist:
                artist = artist.encode("latin-1").decode("utf-8")
            self.ui.setartist(artist)
        if programindex in self.programs:
            programname = self.programs[programindex]['name']
            self.ui.setprogramname(programname)

    def updatealbumart(self, programindex):
        try:
            if self.id3[programindex].xhdr is not None:
                lot = self.id3[programindex].xhdr.lot
                if lot and lot in self.albumart:
                    self.ui.setalbumartdata(self.albumart[lot])
                    return
            if programindex in self.logos:
                self.ui.setalbumartdata(self.logos[programindex])
                return
            elif self.aas_dir is not None:
                logofilename = str(self.frequency) + '-' + str(programindex)
                path = os.path.join(self.aas_dir, logofilename)
                if os.path.exists(path):
                    self.ui.setalbumartfile(path)
                    return
            self.ui.setalbumartdata(None)
            #logging.info("No current album art selected and no logo stored?")
        except Exception as ex:
            self.exceptioninfo(ex)

    def setvolume(self, volume):
        self.volume = volume

    def run(self):
        self.resetdata()

        try:
            freq = float(self.frequency)
            if freq < 87.5 or freq > 107.9:  # TODO: AM?
                raise ValueError
        except ValueError:
            self.ui.setstatus("Invalid frequency")
            return

        self.aas_dir = os.path.join(os.path.dirname(sys.path[0]), "aas")
        if self.cachelogos:
            if not os.path.isdir(self.aas_dir):
                try:
                    os.mkdir(self.aas_dir)
                except Exception as ex:
                    self.exceptioninfo(ex)
                    self.aas_dir = None

        try:
            if self.host:
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

            logging.info("Tuning %s", self.frequency)
            self.ui.setstatus("Tuning %s", self.frequency)

            if freq and freq < 10000:
                freq *= 1e6

            self.radio.set_frequency(freq)

            self.playing = True

            self.audio_thread = threading.Thread(target=self.audio_worker)
            self.audio_thread.start()

            self.radio.start()

        except Exception as ex:
            self.ui.setstatus("Error: %s", self.exceptioninfo(ex))
            self.stop(True)


    def stop(self, *errorstatus):
        if not errorstatus:
            self.ui.setstatus("Stopping")
        logging.info("Stopping")

        if self.playing == True:
            self.playing = False

            try:
                self.radio.stop()
                self.radio.set_bias_tee(0)
                self.radio.close()
            except Exception as ex:
                self.ui.setstatus("Error: %s", self.exceptioninfo(ex))

            for id in self.audio_queues:
                with self.audio_queues[id].mutex:
                    self.audio_queues[id].queue.clear()

            if self.audio_thread != None:
                self.audio_thread.join()

        if not errorstatus:
            self.ui.setstatus("Disconnected")
        logging.info("Disconnected")


    def audio_worker(self):
        audio = pyaudio.PyAudio()
        try:
            index = audio.get_default_output_device_info()["index"]
            stream = audio.open(format=pyaudio.paInt16,
                                channels=2,
                                rate=44100,
                                #frames_per_buffer=2048, #TODO? exe uses 8192?
                                output_device_index=index,
                                output=True)
        except Exception as ex:
            self.exceptioninfo(ex)
            stream = None

        if stream:
            while self.playing:

                # cull inactive/full program buffers.  can we do this without checking every loop?
                for id in self.audio_queues.keys():
                    if id != self.program or self.audio_queues[id].qsize() == self.bufferlength:
                        while self.audio_queues[id].qsize() > self.bufferthresh:
                            try:
                                self.audio_queues[id].get(block=False)
                            except Exception as ex:
                                self.exceptioninfo(ex)
                                continue
                            else:
                                try:
                                    self.audio_queues[id].task_done()
                                except Exception as ex:
                                    self.exceptioninfo(ex)
                                    continue

                if not self.initialbuffer:
                    self.initialbuffer = self.audio_queues[self.program].qsize() >= 16
                #self.initialbuffer = True
                if self.initialbuffer:
                    try:
                        samples = self.audio_queues[self.program].get(block=False)
                    except queue.Empty:
                        #self.initialbuffer = False
                        continue
                    except Exception as ex:
                        self.exceptioninfo(ex)
                        continue
                    else:
                        try:
                            if self.volume < 1:
                                decodeddata = numpy.fromstring(
                                    samples, numpy.int16)
                                newdata = (decodeddata * self.volume).astype(
                                    numpy.int16)
                                stream.write(newdata.tostring())
                            else:
                                stream.write(samples)
                                self.audio_queues[self.program].task_done()
                        except Exception as ex:
                            self.exceptioninfo(ex)
                            continue

            stream.stop_stream()
            stream.close()
        audio.terminate()
        logging.info("Worker Stopped")
