
from DataProcessing import Learner, Filter
from processing_utils import loadBiosig, nanCleaner, \
    find_bad_amplitude_epochs, find_bad_fft_epochs, computeAvgFFT
import math
from DataManipulation import loadDataAsMatrix, readEvents, extractEpochs

import pickle
import numpy as np


class Approach:

    def __init__(self):
        pass

    def defineApproach(self, sample_rate, f_low, f_high, f_order, csp_nei, class_ids, epoch_start, epoch_end):

        self.class_ids = class_ids

        # FEATURE EXTRACTION:
        self.smin = int(math.floor(epoch_start * sample_rate))
        self.smax = int(math.floor(epoch_end * sample_rate))

        self.filter = Filter(f_low, f_high, sample_rate,
                             f_order, filt_type='iir', band_type='band')
        self.learner = Learner()

        self.learner.DesignLDA()
        self.learner.DesignCSP(csp_nei)
        self.learner.AssembleLearner()

    def trainModel(self):

        data, ev = self.loadData(self.data_cal_path, self.events_cal_path)
        epochs, labels = self.loadEpochs(data, ev)
        epochs = self.preProcess(epochs)

        self.learner.Learn(epochs, labels)
        self.learner.EvaluateSet(epochs, labels)
        score = self.learner.GetResults()

        return score

    def validateModel(self):

        data, ev = self.loadData(self.data_val_path, self.events_val_path)
        epochs, labels = self.loadEpochs(data, ev)

        epochs = self.preProcess(epochs)
        self.learner.EvaluateSet(epochs, labels)
        score = self.learner.GetResults()

        return score

    def cross_validate_model(self, n_iter, test_perc):

        data, ev = self.loadData(self.data_cal_path, self.events_cal_path)
        epochs, labels = self.loadEpochs(data, ev)

        epochs = self.preProcess(epochs)

        score = self.learner.cross_evaluate_set(epochs, labels,
                                                n_iter, test_perc)

        return score, self.learner.report[1:], np.mean(self.learner.TFNP_rate[1:], axis=0)

    def applyModelOnDataSet(self, epochs, labels):

        self.learner.EvaluateSet(epochs, labels)
        score = self.learner.GetResults()
        return score

    def applyModelOnEpoch(self, epoch, out_param='label'):

        epoch_f = self.preProcess(epoch)

        if not epoch == []:
            guess = self.learner.EvaluateEpoch(epoch_f, out_param=out_param)
        else:
            guess = None

        return guess

    def setPathToCal(self, dpath, evpath):

        self.data_cal_path = dpath
        self.events_cal_path = evpath

    def setPathToVal(self, dpath, evpath):

        self.data_val_path = dpath
        self.events_val_path = evpath

    def loadData(self, dpath, evpath, data_format='path'):
        if data_format == 'path':
            if self.channels == [-1]:
                data = loadDataAsMatrix(dpath).T
            else:
                data = loadDataAsMatrix(dpath).T[self.channels]

            events = readEvents(evpath)

        elif data_format == 'npy':
            data, events = dpath, evpath

        return data, events

    def loadEpochs(self, data, events):

        epochs, labels = extractEpochs(data, events,
                                       self.smin,
                                       self.smax,
                                       self.class_ids)

        return epochs, labels

    def preProcess(self, data_in):

        data = nanCleaner(data_in)
        data_out = self.filter.ApplyFilter(data)

        return data_out

    def setValidChannels(self, channels):
        self.channels = channels

    def saveToPkl(self, path):
        path += '/approach_info.pkl'

        with open(path, 'w') as file_name:
            pickle.dump(self.__dict__, file_name)

    def loadFromPkl(self, path):
        path += '/approach_info.pkl'

        with open(path, 'r') as file_name:
            load_obj = pickle.load(file_name)

        self.__dict__.update(load_obj)
