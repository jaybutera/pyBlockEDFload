from optparse import OptionParser
import numpy as np
import re

class EDFfile(object):
    def __init__(self, filename):
        self.f = open(filename, 'rb')
        self.signals = np.array([], dtype=object)

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

        #self.data = np.ndarray(shape=(ns, self.gHeader['nrecords']), dtype='<h')

        '''
        scaleFac = [(label['physMax'] - label['physMin']) /
                    (label['digMax'] - label['digMin']) 
                    for label in self.sHeader.values()]
        print scaleFac[0]
        dc = [label['physMax'] - scaleFac[i] *
              label['digMax'] for i, label in enumerate(self.sHeader.values())]
        print dc[0]
        '''

        print 'Header loaded successfully'

    def loadRecords(self):
        print 'Loading requested records...'

        '''
        self.data = dict()
        for label in self.sHeader.items():
            print label[1]['sample']
            self.data[label[0]] = np.zeros(shape=self.gHeader['nrecords']*label[1]['sample'])
        '''

        recordWidth = sum([label['sample'] for label in
            self.sHeader.values()])

        l = self.gHeader['nrecords'] * recordWidth

        sdata = np.fromfile(self.f, dtype='<h', count=l)

        A = np.reshape(sdata, (recordWidth, self.gHeader['nrecords']))
        signalLoc = np.concatenate((np.array([0]), np.cumsum([label['sample']
                                   for label in self.sHeader.values()])))

        for i, sig in enumerate(self.sHeader.values()):
            self.signals = np.append(self.signals, np.reshape(A[signalLoc[i]:signalLoc[i+1],:].T,
                                         sig['sample']*self.gHeader['nrecords']))

        '''
        count = np.zeros(shape=(self.gHeader['ns']))

        for record in xrange(self.gHeader['nrecords']):
            for signal in self.sHeader.items():
                for i in xrange(signal[1]['sample']):
                    count[i] += 1
                    self.data[signal[0]][count] = sdata[sum(count)]
        '''

        '''
        for record in xrange(self.gHeader['nrecords']):
            for i, signal in enumerate(self.sHeader.items()):
                count[i] += 1
                #self.data[signal[0]] = np.append(np.fromfile(self.f, dtype='<h',
                #        count=signal[1]['sample']))
                self.data[signal[0]][count] = np.append(self.data[signal[0]],
                        np.frombuffer(sdata, dtype='<h',
                        count=signal[1]['sample']))
        '''
        '''
        for record in xrange(self.gHeader['nrecords']):
            for signal in self.sHeader.items():
                self.sdata[signal[0]] = np.append(self.data
        '''

        self.f.close()

        print 'Records loaded successfully'

    def digToPhys(self):
        print 'Converting digital signal to uV'

        # Scale data linearly
        scaleFac = [(label['physMax'] - label['physMin']) /
                    (label['digMax'] - label['digMin']) 
                    for label in self.sHeader.values()]
        dc = [label['physMax'] - scaleFac[i] *
              label['digMax'] for i, label in enumerate(self.sHeader.values())]

        for i, signal in enumerate(self.sHeader.keys()):
            self.data[signal] *= scaleFac[i] + dc[i]

    def __del__(self):
        if self.f:
            self.f.close()
            print 'Closing file...'
        print 'Bye bye'

if __name__ == '__main__':
    #signalLabels = []
    filename = ''
    #epochs = ()

    parser = OptionParser()
    #parser.add_option('-l', '--signal_labels', dest = 'signalLabels',
    #        help = 'Signal labels')
    parser.add_option('-f', '--filename', dest = 'filename',
            help = 'Filename for data retrieval')
    #parser.add_option('-e', '--epochs', dest = 'epochs',
    #        help = 'Number of epochs')

    hdr = EDFfile('/Users/jaybutera/Downloads/SC4001E0-PSG.edf')
    hdr.loadHeader()
    hdr.loadRecords()
    #hdr.digToPhys()

    print hdr.signals
