# 5.0168, -2.4674, 16.5087
from optparse import OptionParser
import numpy as np
import re

class EDFfile(object):
    def __init__(self, filename):
        self.f = open(filename, 'rb')

        self.gHeader = dict()
        '''
        'ver' : 0.0,
        'patientID' : '',
        'recordID'  : '',
        'startTime' : '',
        'bytes'     : 0,
        'reserved'  : 0,
        'nrecords'  : 0,
        'duration'  : 0.0,
        'ns'        : 0
        '''

        #self.sHeaders = np.array()
        '''
        'label'      : '',
        'transducer' : '',
        'unit'       : '',
        'physMax'    : 0.0,
        'physMin'    : 0.0,
        'digMax'     : 0.0,
        'digMin'     : 0.0,
        'prefilter'  : '',
        'sample'     : 0,
        'reserved'   : ''
        '''

    def loadHeader(self):
        '''
        Load the Global Header Record into a Header instance.
        '''
        edfHeaderSize = 256;
        datatype = '<h'

        # Global Header Record
        self.gHeader = {
                'ver'       : float(self.f.read(8)),
                'patientID' : self.f.read(80).strip(),
                'recordID'  : self.f.read(80).strip(),
                'startDate' : self.f.read(8),
                'startTime' : self.f.read(8),
                'bytes'     : int(self.f.read(8)),
                'reserved'  : self.f.read(44),
                'nrecords'  : int(self.f.read(8)),
                'duration'  : float(self.f.read(8)),
                'ns'        : int(self.f.read(4))
                }

        ns = self.gHeader['ns']

        # Signal labels
        labels = [re.sub('(?! )\W', '', self.f.read(16)).strip() for label in xrange(ns)] # 7 is temp ns
        labels = [re.sub('  *', '_', label) for label in labels]

        # Signal transducers
        transducers = [self.f.read(80).strip() for transducer in xrange(ns)]

        # Physical dimesions
        units = [self.f.read(8).strip() for unit in xrange(ns)]

        # Physical limits (minimum, maximum)
        physMin = [float(self.f.read(8)) for minimum in xrange(ns)]
        physMax = [float(self.f.read(8)) for maximum in xrange(ns)]

        # Digital limits (minimum, maximum)
        digMin = [float(self.f.read(8)) for minimum in xrange(ns)]
        digMax = [float(self.f.read(8)) for maximum in xrange(ns)]

        # Prefilter
        prefilter = [self.f.read(80).strip() for prefil in xrange(ns)]

        # Samples
        samples = [int(self.f.read(8)) for sample in xrange(ns)]

        reserved = [self.f.read(32) for res in xrange(ns)]

        # Signal headers
        self.sHeaders = np.empty(self.gHeader['ns'], dtype=object)

        for i in xrange(self.gHeader['ns']):
            self.sHeaders[i] = {
                    'label'       : labels[i],
                    'transducer'  : transducers[i],
                    'unit'        : units[i],
                    'physMin'     : physMin[i],
                    'physMax'     : physMax[i],
                    'digMin'      : digMin[i],
                    'digMax'      : digMax[i],
                    'prefilter'   : prefilter[i],
                    'sample'      : samples[i],
                    'reserved'    : reserved[i]
                    }

        print 'Header loaded successfully'

    def loadRecords(self):
        print 'Loading requested records...'

        # Final signal data allocation
        self.signals = np.empty(self.gHeader['ns'], dtype=object)

        recordWidth = sum([int(label['sample']) for label in self.sHeaders])

        # Read signal data from file
        sdata = np.fromfile(self.f, dtype='<h', count=self.gHeader['nrecords']
                                                      * recordWidth)

        A = np.reshape(sdata, (recordWidth, self.gHeader['nrecords']))
        signalLoc = np.concatenate((np.array([0]), np.cumsum([int(label['sample'])
                                    for label in self.sHeaders])))

        for i, sig in enumerate(self.sHeaders):
            self.signals[i] = np.reshape(A[signalLoc[i]:signalLoc[i+1],:],
                    int(sig['sample'])*self.gHeader['nrecords'])
            self.signals[i] = self.signals[i].astype(float)
            #self.signals[i] = np.array(A[signalLoc[i]:signalLoc[i+1],:],
            #        dtype=float)

        self.f.close()

        print 'Records loaded successfully'

    def digToPhys(self):
        print 'Converting digital signal to physical units'

        # Scale data linearly
        scaleFac = np.array([(float(signal['physMax']) - float(signal['physMin'])) /
                    (float(signal['digMax']) - float(signal['digMin'])) for signal in
                    self.sHeaders], dtype=float)

        dc = np.array([signal['physMax'] - scaleFac[i] *
              signal['digMax'] for i, signal in enumerate(self.sHeaders)],
              dtype=float)

        dmin = np.array([signal['digMin'] for signal in self.sHeaders])
        dmax = np.array([signal['digMax'] for signal in self.sHeaders])
        pmin = np.array([signal['physMin'] for signal in self.sHeaders])
        pmax = np.array([signal['physMax'] for signal in self.sHeaders])

        #self.signals = self.signals * scaleFac + dc
        for i in xrange(len(self.signals)):
            self.signals[i] *= scaleFac[i]
            self.signals[i] += dc[i]

        return self.signals

    def __del__(self):
        if self.f:
            self.f.close()
            print 'Closing file...'

if __name__ == '__main__':
    #signalLabels = []
    filename = '/Users/jaybutera/Downloads/SC4001E0-PSG.edf'

    parser = OptionParser()
    #parser.add_option('-l', '--signal_labels', dest = 'signalLabels',
    #        help = 'Signal labels')
    parser.add_option('-f', '--filename', dest = 'filename',
            help = 'Filename for data retrieval')
    #parser.add_option('-e', '--epochs', dest = 'epochs',
    #        help = 'Number of epochs')

    edf = EDFfile(filename)
    edf.loadHeader()
    edf.loadRecords()
    print edf.digToPhys()

