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

        self.sHeader = dict()
        '''
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
        labels=[re.sub('(?! )\W', '', self.f.read(16)).strip() for label in xrange(ns)] # 7 is temp ns
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
            self.sHeaders[i] = np.array([
                labels[i],
                transducers[i],
                units[i],
                physMin[i],
                physMax[i],
                digMin[i],
                digMax[i],
                prefilter[i],
                samples[i],
                reserved[i] ])

        '''
        for i, label in enumerate(labels):
            self.sHeader[label] = {
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
            '''

        print 'Header loaded successfully'

    def loadRecords(self):
        print 'Loading requested records...'
        # Final signal data allocation
        '''
        self.signals = np.recarray(self.gHeader['ns'], dtype=[(label, object) for
            label in self.gHeader.keys()])
        '''
        self.signals = np.empty(self.gHeader['ns'], dtype=object)

        recordWidth = sum([int(label[8]) for label in self.sHeaders])

        # Read signal data from file
        sdata = np.fromfile(self.f, dtype='<h', count=self.gHeader['nrecords']
                                                      * recordWidth)

        A = np.reshape(sdata, (recordWidth, self.gHeader['nrecords']))
        signalLoc = np.concatenate((np.array([0]), np.cumsum([int(label[8])
                                    for label in self.sHeaders])))

        for i, sig in enumerate(self.sHeaders):
            self.signals[i] = np.reshape(A[signalLoc[i]:signalLoc[i+1],:],
                    int(sig[8])*self.gHeader['nrecords'])

        '''
        for i, sig in enumerate(self.sHeader.keys())
            self.signals[sig] = np.reshape(A[signalLoc[i]:signalLoc[i+1],:],
                                         self.sHeader[sig]['sample']*self.gHeader['nrecords'])
        '''

        #print 'self.signals: ', self.signals
        '''
        recordWidth = sum([label['sample'] for label in
            self.sHeader.values()])

        sdata = np.fromfile(self.f, dtype='<h', count=self.gHeader['nrecords']
                                                      * recordWidth)

        A = np.reshape(sdata, (recordWidth, self.gHeader['nrecords']))
        signalLoc = np.concatenate((np.array([0]), np.cumsum([label['sample']
                                    for label in self.sHeader.values()])))

        for i, sig in enumerate(self.sHeader.values()):
            self.signals[i] = np.reshape(A[signalLoc[i]:signalLoc[i+1],:],
                                         sig['sample']*self.gHeader['nrecords'])
        '''

        self.f.close()

        print 'Records loaded successfully'

    def digToPhys(self):
        print 'Converting digital signal to physical units'

        # Scale data linearly
        print type(self.sHeaders[0][4])
        print type(self.sHeaders[0][3])
        print type(self.sHeaders[0][6])
        print type(self.sHeaders[0][5])
        scaleFac = np.array([(float(signal[4]) - float(signal[3])) /
                    (float(signal[6]) - float(signal[5])) for signal in self.sHeaders])
        #scaleFac = scaleFac[::-1]

        dc = np.array([float(signal[4]) - scaleFac[i] *
              float(signal[6]) for i, signal in enumerate(self.sHeaders)])
        #dc = dc[::-1]

        '''
        for i, signal in enumerate([sig[0] for sig in self.signals]):
            print 'signal: ' , signal
            print 'm: ' , scaleFac[i]
            print 'b: ', dc[i]
            print signal * scaleFac[i] + dc[i]
        '''

        '''
        dmin = np.array([float(signal[5]) for signal in self.sHeaders])
        dmax = np.array([float(signal[6]) for signal in self.sHeaders])
        pmin = np.array([float(signal[3]) for signal in self.sHeaders])
        pmax = np.array([float(signal[4]) for signal in self.sHeaders])
        '''

        self.signals *= scaleFac[i] + dc[i]

        '''
        self.signals = (self.signals - dmin) / (dmax-dmin)
        self.signals *= (pmax - pmin) + pmin
        '''
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

    print edf.signals[0]
